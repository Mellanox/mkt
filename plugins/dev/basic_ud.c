#include "basic_ib.h"
#include "basic_tcp.h"

static int _ud_qp_to_rtr(ib_context_t *ctx,
                     int max_send, int max_recv)
{
#define MAX_GATHER_ENTRIES 2
#define MAX_SCATTER_ENTRIES 2
    struct ibv_qp_init_attr attr = {
        .send_cq = ctx->cq,
        .recv_cq = ctx->cq,
        .cap     = {
            .max_send_wr  = max_send,
            .max_recv_wr  = max_recv,
            .max_send_sge = MAX_GATHER_ENTRIES,
            .max_recv_sge = MAX_SCATTER_ENTRIES,
        },
        .qp_type = IBV_QPT_UD,
    };


    ctx->qp = ibv_create_qp(ctx->pd, &attr);
    if (!ctx->qp) {
        fprintf(stderr, "Couldn't create QP\n");
        return -1;
    }

#define WELL_KNOWN_QKEY 0x11111111
    struct ibv_qp_attr qp_modify_attr;
    memset(&qp_modify_attr, 0, sizeof(qp_modify_attr));
    qp_modify_attr.qp_state        = IBV_QPS_INIT;
    qp_modify_attr.pkey_index      = 0;
    qp_modify_attr.port_num        = ctx->s->dev_port;
    qp_modify_attr.qkey            = WELL_KNOWN_QKEY;
    if (ibv_modify_qp(ctx->qp, &qp_modify_attr,
                      IBV_QP_STATE              |
                      IBV_QP_PKEY_INDEX         |
                      IBV_QP_PORT               |
                      IBV_QP_QKEY)) {
        fprintf(stderr, "Failed to modify QP to INIT\n");
        goto free_qp;
    }

    memset(&qp_modify_attr, 0, sizeof(qp_modify_attr));
    qp_modify_attr.qp_state = IBV_QPS_RTR;

    if (ibv_modify_qp(ctx->qp, &qp_modify_attr, IBV_QP_STATE)) {
        fprintf(stderr, "Failed to modify QP to RTR\n");
        goto free_qp;
    }

    return 0;
free_qp:
    ibv_destroy_qp(ctx->qp);
    return -1;
}

int init_ud_recv(ib_context_t *ctx)
{
    int ret;
#define MAX_NUM_RECVS 0x10
    ret = _ud_qp_to_rtr(ctx, 0, MAX_NUM_RECVS);
    exchange_recv(ctx);
    return ret;
}

int init_ud_send(ib_context_t *ctx)
{
    int ret = 0;
#define MAX_NUM_SENDS 0x10
    ret = _ud_qp_to_rtr(ctx, MAX_NUM_SENDS, 0);
    if (ret){
        return ret;
    }

    struct ibv_qp_attr qp_modify_attr = { 0 };
    qp_modify_attr.qp_state	    = IBV_QPS_RTS;

    if (ibv_modify_qp(ctx->qp, &qp_modify_attr,
                      IBV_QP_STATE | IBV_QP_SQ_PSN)) {
        fprintf(stderr, "Failed to modify QP to RTS\n");
        goto free_qp;
    }
    exchange_send(ctx);

free_qp:
    ibv_destroy_qp(ctx->qp);
    return -1;
}

int send_ud(ib_context_t *ctx, int size)
{
    struct ibv_send_wr wr;
    struct ibv_sge list;
    struct ibv_ah *ah = NULL;
    int ret;

    ah = get_ah(ctx);
    if (!ah) {
        fprintf(stderr, "Failed to create address handle\n");
        return -1;
    }

    list.addr   = (uint64_t)ctx->mr_buffer;
    list.length = size;
    list.lkey   = ctx->mr->lkey;

    wr.wr_id      = 0;
    wr.sg_list    = &list;
    wr.num_sge    = 1;
    wr.opcode     = IBV_WR_SEND;
    wr.send_flags = IBV_SEND_SIGNALED;
    wr.next       = NULL;

    wr.wr.ud.ah = ah;
    wr.wr.ud.remote_qpn  = ctx->s->dqpn;
    wr.wr.ud.remote_qkey = WELL_KNOWN_QKEY;

    ret = send_wr(ctx, &wr);
    ibv_destroy_ah(ah);
    return ret;
}
