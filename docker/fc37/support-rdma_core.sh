#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: f58a9b64ae717493979326514e90608b796c7ebd

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
