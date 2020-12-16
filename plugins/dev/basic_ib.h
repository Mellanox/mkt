#ifndef BASIC_IB_COMMON_H
#define BASIC_IB_COMMON_H

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <infiniband/verbs.h>

typedef struct {
    char host[64];
    uint16_t tcp_port;
    char devname[64];
    int  dev_port;
    int  llid;
    int  dlid;
    int  lqpn;
    int  dqpn;
    union ibv_gid lgid;
    union ibv_gid dgid;
} settings_t;

#define REGION_SIZE 0x1800

typedef struct {
    settings_t *s;
    struct ibv_context *ctx;
    struct ibv_device *dev;
    struct ibv_pd *pd;
    char mr_buffer[REGION_SIZE];
    struct ibv_mr *mr;
    struct ibv_cq *cq;
    struct ibv_qp *qp;
} ib_context_t;

void usage(const char *argv0, int is_send);
int parse_args(int argc, char **argv, settings_t *s, int is_send);
//int parse_gid(char *gid_str, union ibv_gid *gid);
int init_ctx(ib_context_t *ctx, settings_t *s);
void free_ctx(ib_context_t *ctx);
int recv_loop(ib_context_t *ctx);
int send_wr(ib_context_t *ctx, struct ibv_send_wr *wr);
struct ibv_ah *get_ah(ib_context_t *ctx);


#endif // BASIC_IB_COMMON_H
