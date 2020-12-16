#ifndef BASIC_TCP_H
#define BASIC_TCP_H

#include "basic_ib.h"

int exchange_send(ib_context_t *ctx);
int exchange_recv(ib_context_t *ctx);

#endif // BASIC_TCP_H
