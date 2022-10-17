#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: 196bad56ed060612e22674b668b5ec3d8659ade3

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
