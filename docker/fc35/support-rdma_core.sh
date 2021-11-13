#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: ab6b2ecad72140ef2e82a120bbd8e00b913fdde8

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
