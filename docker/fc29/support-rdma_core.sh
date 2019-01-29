#!/bin/bash
# ---
# git_url: /images/leonro/src/rdma-core
# git_commit: 988936bf

rpmbuild --build-in-place -bb redhat/rdma-core.spec
