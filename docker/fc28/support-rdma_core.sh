#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: v20

rpmbuild --build-in-place -bb redhat/rdma-core.spec
