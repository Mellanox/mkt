#if HAVE_CONFIG_H
#  include <config.h>
#endif /* HAVE_CONFIG_H */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netdb.h>
#include <malloc.h>
#include <getopt.h>
#include <arpa/inet.h>
#include <time.h>
#include <infiniband/verbs.h>



static void usage(const char *argv0)
{
	printf("Usage:\n");
	printf("  %s send packets to remote\n", argv0);
	printf("\n");
	printf("Options:\n");
	printf("  -d, --dev-name=<dev>   use  device <dev>)\n");
	printf("  -i, --dev_port=<port>  use port <port> of device (default 1)\n");
	printf("  -l, --dest_lid=<lid>  use lid as remote lid on destination port (Infiniband only)\n");
	printf("  -g, --dest_gid=<gid>  use gid as remote gid on destination port\n");
	printf("          <gid format>=xxxx:xxxx:xxxx:xxxx\n");
	printf("  -q, --dest_qpn=<qpn>  use qpn for remote queue pair number\n");
}

static int parse_gid(char *gid_str, union ibv_gid *gid) {
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


int main(int argc, char *argv[]) {
	char *devname = NULL;
	int   dev_port = 1;
	int num_devices;
	char *dest_gid_str;
	int   dest_lid = 0;
	int   dest_qpn = 0;


	static struct option long_options[] = {
		{ .name = "dev-name",  .has_arg = 1, .val = 'd' },
		{ .name = "dev-port",  .has_arg = 1, .val = 'i' },
		{ .name = "dest-gid",  .has_arg = 1, .val = 'g' },
		{ .name = "dest-lid",  .has_arg = 1, .val = 'l' },
		{ .name = "dest-qpn",  .has_arg = 1, .val = 'q' }
	};


	while (1) {
		int c;

		c = getopt_long(argc, argv, "p:d:i:g:q:l:",
				long_options, NULL);
		if (c == -1)
			break;

		switch (c) {
		case 'd':
			devname = strdup(optarg);
			break;

		case 'i':
			dev_port = strtol(optarg, NULL, 0);
			if (dev_port < 0) {
				usage(argv[0]);
				return 1;
			}
			break;
		case 'g':
			dest_gid_str = strdup(optarg);
			break;

		case 'l':
			dest_lid = strtol(optarg, NULL, 0);
			if (dest_lid < 0) {
				usage(argv[0]);
				return 1;
			}
			break;
		case 'q':
			dest_qpn = strtol(optarg, NULL, 0);
			if (dest_qpn < 0) {
				usage(argv[0]);
				return 1;
			}
			break;

		default:
			usage(argv[0]);
			return 1;
		}
	}


	struct ibv_device **dev_list = ibv_get_device_list(&num_devices);
	if (!dev_list) {
		perror("Failed to get RDMA devices list");
		return 1;
	}

	int i;
	for (i = 0; i < num_devices; ++i)
		if (!strcmp(ibv_get_device_name(dev_list[i]), devname))
			break;

	if (i == num_devices) {
		fprintf(stderr, "RDMA device %s not found\n", devname);
		goto  free_dev_list;
	}

	struct ibv_device *device  = dev_list[i];

	struct ibv_context *context = ibv_open_device(device);
	if (!context) {
		fprintf(stderr, "Couldn't get context for %s\n",
				ibv_get_device_name(device));
		goto free_dev_list;
	}

	struct ibv_pd *pd = ibv_alloc_pd(context);
	if (!pd) {
		fprintf(stderr, "Couldn't allocate PD\n");
		goto close_device;
	}

#define REGION_SIZE 0x1800
	char mr_buffer[REGION_SIZE];

	struct ibv_mr *mr = ibv_reg_mr(pd, mr_buffer, REGION_SIZE, 0);
	if (!mr) {
		fprintf(stderr, "Couldn't register MR\n");
		goto close_pd;
	}

#define CQ_SIZE 0x100

	struct ibv_cq *cq = ibv_create_cq(context, CQ_SIZE, NULL,
			NULL, 0);
	if (!cq) {
		fprintf(stderr, "Couldn't create CQ\n");
		goto free_mr;
	}

#define MAX_NUM_SENDS 0x10
#define MAX_GATHER_ENTRIES 2
#define MAX_SCATTER_ENTRIES 2

	struct ibv_qp_init_attr attr = {
		.send_cq = cq,
		.recv_cq = cq,
		.cap     = {
			.max_send_wr  = MAX_NUM_SENDS,
			.max_recv_wr  = 0,
			.max_send_sge = MAX_GATHER_ENTRIES,
			.max_recv_sge = MAX_SCATTER_ENTRIES,
		},
		.qp_type = IBV_QPT_UD,
	};


	struct ibv_qp *qp = ibv_create_qp(pd, &attr);
	if (!qp) {
		fprintf(stderr, "Couldn't create QP\n");
		goto free_cq;
	}

	struct ibv_qp_attr qp_modify_attr;

#define WELL_KNOWN_QKEY 0x11111111

	qp_modify_attr.qp_state        = IBV_QPS_INIT;
	qp_modify_attr.pkey_index      = 0;
	qp_modify_attr.port_num        = dev_port;
	qp_modify_attr.qkey            = WELL_KNOWN_QKEY;
	if (ibv_modify_qp(qp, &qp_modify_attr,
				IBV_QP_STATE              |
				IBV_QP_PKEY_INDEX         |
				IBV_QP_PORT               |
				IBV_QP_QKEY)) {
		fprintf(stderr, "Failed to modify QP to INIT\n");
		goto free_qp;
	}


	qp_modify_attr.qp_state		= IBV_QPS_RTR;

	if (ibv_modify_qp(qp, &qp_modify_attr, IBV_QP_STATE)) {
		fprintf(stderr, "Failed to modify QP to RTR\n");
		goto free_qp;
	}

	qp_modify_attr.qp_state	    = IBV_QPS_RTS;

	if (ibv_modify_qp(qp, &qp_modify_attr, IBV_QP_STATE
				| IBV_QP_SQ_PSN)) {
		fprintf(stderr, "Failed to modify QP to RTS\n");
		goto free_qp;
	}

	union ibv_gid dest_gid;

	if (parse_gid(dest_gid_str, &dest_gid)) {
		usage(argv[0]);
		return -1;
	}

	struct ibv_ah_attr ah_attr;

	ah_attr.is_global  = 1;
	ah_attr.grh.dgid = dest_gid;
	ah_attr.grh.sgid_index = 0;
	ah_attr.grh.hop_limit = 1;
	ah_attr.sl = 0;
	ah_attr.dlid = dest_lid;
	ah_attr.port_num = dev_port;

	struct ibv_ah *ah;

	ah = ibv_create_ah(pd, &ah_attr);
	if (!ah) {
		fprintf(stderr, "Failed to create address handle\n");
		goto free_qp;
	}

	struct ibv_send_wr wr;
	struct ibv_send_wr *bad_wr;
	struct ibv_sge list;
	struct ibv_wc wc;
	int ne;

#define TEXT_MSG "Hello UD :)"

	sprintf(mr_buffer, TEXT_MSG);
	list.addr   = (uint64_t)mr_buffer;
	list.length = strlen(TEXT_MSG);
	list.lkey   = mr->lkey;


	wr.wr_id      = 0;
	wr.sg_list    = &list;
	wr.num_sge    = 1;
	wr.opcode     = IBV_WR_SEND;
	wr.send_flags = IBV_SEND_SIGNALED;
	wr.next       = NULL;

	wr.wr.ud.ah = ah;
	wr.wr.ud.remote_qpn  = dest_qpn;
	wr.wr.ud.remote_qkey = WELL_KNOWN_QKEY;


	printf("Ready for post send\n");
	scanf("%*d");
	if (ibv_post_send(qp,&wr,&bad_wr)) {
		fprintf(stderr, "Function ibv_post_send failed\n");
		return 1;
	}

	do { ne = ibv_poll_cq(cq, 1,&wc);} while (ne == 0);
	if (ne < 0) {
		fprintf(stderr, "CQ is in error state");
		return 1;
	}

	if (wc.status) {
		fprintf(stderr, "Bad completion (status %d)\n",(int)wc.status);
		return 1;
	}

free_qp:
	ibv_destroy_qp(qp);

free_cq:
	ibv_destroy_cq(cq);

free_mr:
	ibv_dereg_mr(mr);

close_pd:
	ibv_dealloc_pd(pd);

close_device:
	ibv_close_device(context);

free_dev_list:
	ibv_free_device_list(dev_list);

	return 0;
}





