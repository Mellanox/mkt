#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <poll.h>
#include <errno.h>

#include "basic_ib.h"

#define PACK_ELEM(dst, dst_size, src, src_size)  \
{                                                            \
    if (dst_size < src_size) {                               \
        fprintf(stderr, "%s:%d: Failed to pack element!\n",  \
                      __FILE__,__LINE__);                    \
        exit(1);                                             \
    }                                                        \
    memcpy(dst, src, src_size);                              \
    dst += src_size;                                         \
    dst_size -= src_size;                                    \
}

#define UNPACK_ELEM(dst, dst_size, src, src_size)              \
{                                                              \
    if (src_size < dst_size) {                                 \
        fprintf(stderr, "%s:%d: Failed to unpack element!\n",  \
                      __FILE__,__LINE__);                      \
        exit(1);                                               \
    }                                                          \
    memcpy(dst, src, dst_size);                                \
    src += dst_size;                                           \
    src_size -= dst_size;                                      \
}


ssize_t pack_ep(ib_context_t *ctx, char *buf, ssize_t max_len)
{
    char *ptr = buf;
    ssize_t remain = max_len;

    PACK_ELEM(ptr, remain, &ctx->s->llid, sizeof(ctx->s->llid));
    PACK_ELEM(ptr, remain, &ctx->s->lqpn, sizeof(ctx->s->lqpn));
    return max_len - remain;
}

ssize_t unpack_ep(ib_context_t *ctx, char *buf, ssize_t max_len)
{
    char *ptr = buf;
    ssize_t remain = max_len;

    UNPACK_ELEM(&ctx->s->dlid, sizeof(ctx->s->dlid), ptr, remain);
    UNPACK_ELEM(&ctx->s->dqpn, sizeof(ctx->s->dqpn), ptr, remain);
    return max_len - remain;
}


int exchange_send(ib_context_t *ctx)
{
    int sock, n;
    struct sockaddr_in addr;
    struct addrinfo *res, *t;
    struct addrinfo hints = { 0 };
    char service[64];
    char message[64] = {0}, *mptr = message;
    ssize_t len = 0;

    hints.ai_family   = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    sprintf(service, "%d", ctx->s->tcp_port);
    n = getaddrinfo(ctx->s->host, service, &hints, &res);

    if (n < 0) {
        fprintf(stderr, "%s for %s:%s\n", gai_strerror(n), ctx->s->host, service);
        fprintf(stderr, "%s:%d: getaddrinfo failed!\n", __FILE__,__LINE__);
        exit(1);
    }

    for (t = res; t; t = t->ai_next) {
        sock = socket(t->ai_family, t->ai_socktype, t->ai_protocol);
        if (sock >= 0) {
            if (!connect(sock, t->ai_addr, t->ai_addrlen))
                break;
            close(sock);
            sock = -1;
        }
    }

    freeaddrinfo(res);

    len = pack_ep(ctx, message, sizeof(message));
    if (len != send(sock, message, len, 0)) {
        fprintf(stderr, "%s:%d: Failed to send the endpoint information: %zd!\n",
                __FILE__,__LINE__, len);
        exit(1);
    }

    if (0 >= (len = recv(sock, message, sizeof(message), 0))) {
        fprintf(stderr, "%s:%d: Failed to recv the endpoint information: %zd!\n",
                __FILE__,__LINE__, len);
        exit(1);
    }

    len = unpack_ep(ctx, message, len);
    if (len) {
        fprintf(stderr, "%s:%d: Failed to unpack the endpoint information!\n",
                __FILE__,__LINE__);
        exit(1);
    }

    close(sock);
    return 0;
}

int exchange_recv(ib_context_t *ctx)
{
    int sock, listener;
    struct sockaddr_in addr;
    char message[64];
    ssize_t len;

    listener = socket(AF_INET, SOCK_STREAM, 0);
    if(listener < 0)
    {
        perror("socket");
        exit(1);
    }

    addr.sin_family = AF_INET;
    addr.sin_port = htons(ctx->s->tcp_port);
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    if(bind(listener, (struct sockaddr *)&addr, sizeof(addr)) < 0)
    {
        perror("bind");
        exit(2);
    }

    listen(listener, 1);

    sock = accept(listener, NULL, NULL);
    if(sock < 0)
    {
        perror("accept");
        exit(1);
    }

    if (0 >= (len = recv(sock, message, sizeof(message), 0))) {
        fprintf(stderr, "%s:%d: Failed to recv the endpoint information: %zd!\n",
                __FILE__,__LINE__, len);
        exit(1);
    }
    len = unpack_ep(ctx, message, len);
    if (len) {
        fprintf(stderr, "%s:%d: Failed to unpack the endpoint information!\n",
                __FILE__,__LINE__);
        exit(1);
    }

    len = pack_ep(ctx, message, sizeof(message));
    if (len != send(sock, message, len, 0)) {
        fprintf(stderr, "%s:%d: Failed to send the endpoint information: %zd!\n",
                __FILE__,__LINE__, len);
        exit(1);
    }

    close(sock);
    return 0;
}
