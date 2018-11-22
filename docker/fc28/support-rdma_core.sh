#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: v21

rpmbuild --build-in-place -bb redhat/rdma-core.spec
