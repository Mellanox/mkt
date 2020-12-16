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

#include "basic_ib.h"
#include "basic_ud.h"

int main(int argc, char *argv[])
{
    settings_t settings, *s = &settings;
    ib_context_t ib_ctx, *ctx = &ib_ctx;

    parse_args(argc, argv, s, 1);
    init_ctx(ctx, s);
    init_ud_send(ctx);

#define TEXT_MSG "Hello UD :)"
    sprintf(ctx->mr_buffer, TEXT_MSG);
    if (send_ud(ctx, strlen(TEXT_MSG))){
        fprintf(stderr, "Failed to send message\n");
        goto exit;
    }

exit:
    free_ctx(ctx);
    return 0;
}





