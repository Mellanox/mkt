#include "basic_ib.h"
#include <getopt.h>
#include <string.h>
#include <arpa/inet.h>

#define DEFAULT_TCP_PORT 1807

void usage(const char *argv0, int is_send)
{
    printf("Usage:\n");
    printf("  %s send packets to remote\n", argv0);
    printf("\n");
    printf("Options:\n");
    printf("  -d, --dev-name=<dev>   use  device <dev>)\n");
    printf("  -i, --dev_port=<port>  use port <port> of device (default 1)\n");
    if( is_send) {
        printf("  -h, --host=<host>  Connect to the host <host>)\n");
    }
    printf("  -p, --port=<port>  TCP port <port> for endpoint exchange (default is %d)\n",
           DEFAULT_TCP_PORT);
}


static struct option long_options[] = {
    { .name = "dev-name",  .has_arg = 1, .val = 'd' },
    { .name = "dev-port",  .has_arg = 1, .val = 'i' },
    { .name = "host",  .has_arg = 1, .val = 'h' },
    { .name = "port",  .has_arg = 1, .val = 'p' },
};

int parse_args(int argc, char **argv, settings_t *s, int is_send)
{
    memset(s, 0, sizeof(*s));
    char *opts_str = NULL;

    if(is_send) {
        opts_str = "d:i:h:p:";
    } else {
        opts_str = "d:i:p:";
    }

    s->dev_port = 1;
    s->tcp_port = DEFAULT_TCP_PORT;

    while (1) {
        int c;

        c = getopt_long(argc, argv, opts_str,
                        long_options, NULL);
        if (c == -1)
            break;

        switch (c) {
        case 'h':
            strcpy(s->host, optarg);
            break;

        case 'p':
            s->tcp_port = strtol(optarg, NULL, 0);
            if (s->tcp_port < 0) {
                usage(argv[0], is_send);
                return 1;
            }
            break;

        case 'd':
            strcpy(s->devname, optarg);
            break;

        case 'i':
            s->dev_port = strtol(optarg, NULL, 0);
            if (s->dev_port < 0) {
                usage(argv[0], is_send);
                return 1;
            }
            break;

        default:
            usage(argv[0], is_send);
            return 1;
        }
    }
}

#if 0
int parse_gid(char *gid_str, union ibv_gid *gid) {
    uint16_t mcg_gid[8];
    char *ptr = gid_str;
    char *term = gid_str;
    int i = 0;

    term = strtok(gid_str, ":");
    while(1){
        mcg_gid[i] = htons((uint16_t)strtoll(term, NULL, 16));

        term = strtok(NULL, ":");
        if (term == NULL)
            break;

        if ((term - ptr) != 5) {
            fprintf(stderr, "Invalid GID format.\n");
            return -1;
        }
        ptr = term;

        i += 1;
    };

    if (i != 7) {
        fprintf(stderr, "Invalid GID format (2).\n");
        return -1;
    }

    memcpy(gid->raw, mcg_gid,16);
    return 0;
}
#endif

struct ibv_ah *get_ah(ib_context_t *ctx)
{
    struct ibv_ah_attr ah_attr;
    ah_attr.is_global  = 0;
    ah_attr.sl = 0;
    ah_attr.dlid = ctx->s->dlid;
    ah_attr.port_num = ctx->s->dev_port;

    return ibv_create_ah(ctx->pd, &ah_attr);
}

int init_ctx(ib_context_t *ctx, settings_t *s)
{
    int num_devices, ret = -1;
    ctx->s = s;
    memset(ctx, 0, sizeof(*ctx));

    struct ibv_device **dev_list = ibv_get_device_list(&num_devices);
    if (!dev_list) {
        perror("Failed to get RDMA devices list");
        return ret;
    }

    int i;
    for (i = 0; i < num_devices; ++i)
        if (!strcmp(ibv_get_device_name(dev_list[i]), s->devname))
            break;

    if (i == num_devices) {
        fprintf(stderr, "RDMA device %s not found\n", s->devname);
        goto  free_dev_list;
    }

    ctx->dev = dev_list[i];

    ctx->ctx = ibv_open_device(ctx->dev);
    if (!ctx->ctx) {
        fprintf(stderr, "Couldn't get context for %s\n",
                ibv_get_device_name(ctx->dev));
        goto free_dev_list;
    }

    struct ibv_port_attr pattrs;
    if (ibv_query_port(ctx->ctx, ctx->s->dev_port, &pattrs)) {
        fprintf(stderr, "Couldn't Query port %d for %s\n",
                ctx->s->dev_port, ibv_get_device_name(ctx->dev));
        goto free_dev_list;
    }

    ctx->s->llid = pattrs.lid;

    ctx->pd = ibv_alloc_pd(ctx->ctx);
    if (!ctx->pd) {
        fprintf(stderr, "Couldn't allocate PD\n");
        goto close_device;
    }

    ctx->mr = ibv_reg_mr(ctx->pd, ctx->mr_buffer, REGION_SIZE, 0);
    if (!ctx->mr) {
        fprintf(stderr, "Couldn't register MR\n");
        goto close_pd;
    }

#define CQ_SIZE 0x100

    ctx->cq = ibv_create_cq(ctx->ctx, CQ_SIZE, NULL,
                            NULL, 0);
    if (!ctx->cq) {
        fprintf(stderr, "Couldn't create CQ\n");
        goto free_mr;
    }

    ret = 0;
    goto free_dev_list;

free_mr:
    ibv_dereg_mr(ctx->mr);

close_pd:
    ibv_dealloc_pd(ctx->pd);

close_device:
    ibv_close_device(ctx->ctx);

free_dev_list:
    ibv_free_device_list(dev_list);
    return ret;
}

void free_ctx(ib_context_t *ctx)
{
    if(ctx->qp){
        ibv_destroy_qp(ctx->qp);
    }
    ibv_destroy_cq(ctx->cq);
    ibv_dereg_mr(ctx->mr);
    ibv_dealloc_pd(ctx->pd);
    ibv_close_device(ctx->ctx);
}

int recv_loop(ib_context_t *ctx)
{
    struct ibv_recv_wr wr;
    struct ibv_recv_wr *bad_wr;
    struct ibv_sge list;
    struct ibv_wc wc;
    int ne, i;

#define MAX_MSG_SIZE 0x100

    while( 1 ) {
        for (i = 0; i < 4; i++) {
            list.addr   = (uint64_t)(ctx->mr_buffer + MAX_MSG_SIZE*i);
            list.length = MAX_MSG_SIZE;
            list.lkey   = ctx->mr->lkey;


            wr.wr_id      = i;
            wr.sg_list    = &list;
            wr.num_sge    = 1;
            wr.next       = NULL;

            if (ibv_post_recv(ctx->qp, &wr, &bad_wr)) {
                fprintf(stderr, "Function ibv_post_recv failed\n");
                return 1;
            }
        }

        i = 0;
        while (i < 4) {
            do { ne = ibv_poll_cq(ctx->cq, 1,&wc);}  while (ne == 0);
            if (ne < 0) {
                fprintf(stderr, "CQ is in error state");
                return 1;
            }

            if (wc.status) {
                fprintf(stderr, "Bad completion (status %d)\n",(int)wc.status);
                return 1;
            } else {
                printf("received: %s\n", ctx->mr_buffer + MAX_MSG_SIZE*i +
                       40);
            }

            i++;
        }
        printf("Press enter to respost\n");
        getchar();
    }
}

int send_wr(ib_context_t *ctx, struct ibv_send_wr *wr)
{
    struct ibv_send_wr *bad_wr;
    struct ibv_wc wc;
    int ne;

    printf("Ready for post send\n");
    scanf("%*d");
    if (ibv_post_send(ctx->qp, wr,&bad_wr)) {
        fprintf(stderr, "Function ibv_post_send failed\n");
        return -1;
    }

    do {
        ne = ibv_poll_cq(ctx->cq, 1, &wc);
    } while (ne == 0);

    if (ne < 0) {
        fprintf(stderr, "CQ is in error state");
        return -1;
    }

    if (wc.status) {
        fprintf(stderr, "Bad completion (status %d)\n",(int)wc.status);
        return -1;
    }
    return 0;
}
