#ifndef BASIC_RC_H
#define BASIC_RC_H

int init_rc_recv(ib_context_t *ctx);
int init_rc_send(ib_context_t *ctx);
int send_rc(ib_context_t *ctx, int size);

#endif // BASIC_RC_H
