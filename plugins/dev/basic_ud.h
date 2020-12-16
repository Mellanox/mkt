#ifndef BASIC_UD_COMMON_H
#define BASIC_UD_COMMON_H

#include "basic_ib.h"

int init_ud_recv(ib_context_t *ctx);
int init_ud_send(ib_context_t *ctx);
int send_ud(ib_context_t *ctx, int size);

#endif // BASIC_UD_COMMON_H
