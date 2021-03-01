#!/bin/bash
# ---
# git_url: https://github.com/linux-rdma/rdma-core.git
# git_commit: 7f2d460ff23393840088b5ea18df920cea0ee418

rpmbuild --build-in-place -bb redhat/rdma-core.spec --with pyverbs
