#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: 30567e133dccca942df146199205f8df8dd89c97

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
