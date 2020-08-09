#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: 568ad09e682e300befd64a6b2dd99b9fc8c90999

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
