#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: 559083a154af62e02815969c337e90ef4c3cd173

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
