#!/bin/bash
# ---
# git_url: /mswg/git/Linux_drivers_verification/drivertest.git/
# git_commit: rel-00_10_0018
# image_files:
#   local_mkt/support_rdma_core:fc29:
#       dest: /opt/rdma-core/
#       files:
#          - /root/rpmbuild/RPMS/x86_64/*.rpm

rpmbuild --build-in-place -bb drivertest.spec