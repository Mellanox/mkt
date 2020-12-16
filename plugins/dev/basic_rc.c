#include "basic_ib.h"
#include "basic_tcp.h"

static int _rc_qp_to_rts(ib_context_t *ctx, int is_send, int max_wr_cnt)
{
#define MAX_GATHER_ENTRIES 2
#define MAX_SCATTER_ENTRIES 2

    struct ibv_qp_init_attr attr = { 0 };
    attr.send_cq = ctx->cq;
    attr.recv_cq = ctx->cq;
    if(is_send) {
        attr.cap.max_send_wr  = max_wr_cnt;
    } else {
        attr.cap.max_recv_wr  = max_wr_cnt;
    }
    attr.cap.max_send_sge = MAX_GATHER_ENTRIES;
    attr.cap.max_recv_sge = MAX_SCATTER_ENTRIES;
    attr.qp_type = IBV_QPT_RC;

    ctx->qp = ibv_create_qp(ctx->pd, &attr);
    if (!ctx->qp) {
        fprintf(stderr, "Couldn't create QP\n");
        return 1;
    }

    struct ibv_qp_attr qp_modify_attr = { 0 };

    qp_modify_attr.qp_state        = IBV_QPS_INIT;
    qp_modify_attr.pkey_index      = 0;
    qp_modify_attr.port_num        = ctx->s->dev_port;
    qp_modify_attr.qp_access_flags = 0;
    if (ibv_modify_qp(ctx->qp, &qp_modify_attr,
                      IBV_QP_STATE              |
                      IBV_QP_PKEY_INDEX         |
                      IBV_QP_PORT               |
                      IBV_QP_ACCESS_FLAGS)) {
        fprintf(stderr, "Failed to modify QP to INIT\n");
        return 1;
    }

    if (is_send) {
        exchange_send(ctx);
    } else {
        exchange_recv(ctx);
    }

    memset(&qp_modify_attr, 0, sizeof(qp_modify_attr));
    qp_modify_attr.qp_state           = IBV_QPS_RTR;
    qp_modify_attr.path_mtu           = 4096;
    qp_modify_attr.dest_qp_num        = ctx->s->dqpn;
    qp_modify_attr.rq_psn             = 0;
    qp_modify_attr.max_dest_rd_atomic = 1;
    qp_modify_attr.min_rnr_timer      = 12;
    qp_modify_attr.ah_attr.is_global	= 0;
    qp_modify_attr.ah_attr.dlid		= ctx->s->dlid;
    qp_modify_attr.ah_attr.sl         = 0;
    qp_modify_attr.ah_attr.src_path_bits	= 0;
    qp_modify_attr.ah_attr.port_num	= ctx->s->dev_port;
    if (ibv_modify_qp(ctx->qp, &qp_modify_attr,
                      IBV_QP_STATE              |
                      IBV_QP_AV                 |
                      IBV_QP_PATH_MTU           |
                      IBV_QP_DEST_QPN           |
                      IBV_QP_RQ_PSN             |
                      IBV_QP_MAX_DEST_RD_ATOMIC |
                      IBV_QP_MIN_RNR_TIMER      |
                      IBV_QP_TIMEOUT)) {
        fprintf(stderr, "Failed to modify QP to RTR\n");
        return 1;
    }

    memset(&qp_modify_attr, 0, sizeof(qp_modify_attr));
    qp_modify_attr.qp_state       = IBV_QPS_RTS;
    qp_modify_attr.rnr_retry      = 7;
    qp_modify_attr.sq_psn         = 0;
    qp_modify_attr.max_rd_atomic  = 1;

    /* Setup the send retry parameters:
     *  - timeout (see [1] for details on how to calculate)
     *    $ Value of 23 corresponds to 34 sec
     *  - retry_cnt (max is 7 times)
     * Max timeout is (retry_cnt * timeout)
     *  - 7 * 34s = 231s = 3 m
     * [1] https://www.rdmamojo.com/2013/01/12/ibv_modify_qp/
     */
    qp_modify_attr.timeout            = 23;
    qp_modify_attr.retry_cnt          = 7;

    if (ibv_modify_qp(ctx->qp, &qp_modify_attr,
                      IBV_QP_STATE              |
                      IBV_QP_TIMEOUT            |
                      IBV_QP_RETRY_CNT          |
                      IBV_QP_RNR_RETRY          |
                      IBV_QP_SQ_PSN             |
                      IBV_QP_MAX_QP_RD_ATOMIC)) {
        fprintf(stderr, "Failed to modify QP to RTS\n");
        return 1;
    }
    return 0;
}

int init_rc_recv(ib_context_t *ctx, settings_t *s)
{
    int ret;
#define MAX_NUM_RECVS 0x10
    ret = _rc_qp_to_rts(ctx, 0, MAX_NUM_RECVS);
    return ret;
}

int init_rc_send(ib_context_t *ctx, settings_t *s)
{
    int ret;
#define MAX_NUM_SENDS 0x10
    ret = _rc_qp_to_rts(ctx, 1, MAX_NUM_SENDS);
    return ret;
}

int send_rc(ib_context_t *ctx, int size)
{
    struct ibv_sge list;
    struct ibv_send_wr wr;

    memset(&list, 0, sizeof(list));
    list.addr = (uintptr_t)ctx->mr_buffer;
    list.length = size;
    list.lkey = ctx->mr->lkey;

    memset(&wr, 0, sizeof(wr));
    wr.wr_id        = (uint64_t)0;
    wr.sg_list    = &list;
    wr.num_sge    = 1;
    wr.opcode     = IBV_WR_SEND;
    wr.send_flags = IBV_SEND_SIGNALED;

    return send_wr(ctx, &wr);
}
