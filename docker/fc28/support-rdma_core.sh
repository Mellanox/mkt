#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: 4e012421062f9013e1729d410c8b2c53e4ec92ee

rpmbuild --build-in-place -bb redhat/rdma-core.spec
