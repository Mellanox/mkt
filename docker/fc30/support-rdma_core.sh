#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: 0612a133214384e68fac17a34f8f6131313b7804

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
