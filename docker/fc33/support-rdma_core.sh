#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: c04e11d8bfe6febe3ea9e8b1bb52bee94c650af6

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
