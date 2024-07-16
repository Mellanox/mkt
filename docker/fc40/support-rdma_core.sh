#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: d74b9602d50f24f535e7a5f375b1a177426e904c

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
