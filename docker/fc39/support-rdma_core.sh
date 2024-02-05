#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: 6c75a8c4b8f6bb7ff6f74df20cd8f6be27fda0fa

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
