#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: cc7e5eb56579d6fc02019c0067da4e17afef8312

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
