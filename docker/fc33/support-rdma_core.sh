#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: 426e3298f91199c82c10705761eb996551695604
# other_files:
#  - 0001-build-Disable-LTO-for-FC33-builds.patch
#  - 0002-redhat-Provide-ninja-directory.patch
#  - 0003-redhat-Fix-wrong-installation-path-of-ib_acm.patch

patch -p1 < /opt/0001-*.patch
patch -p1 < /opt/0002-*.patch
patch -p1 < /opt/0003-*.patch

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
