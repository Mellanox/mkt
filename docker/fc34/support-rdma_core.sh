#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: 83ebc349dcd54761f952bc4305ead392fe874718

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
