#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: e29a698e99028e9a092bb00c03ee4bfa31ae0cf3

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
