#!/bin/bash
# ---
# git_url: https://github.com/HewlettPackard/netperf.git
# git_commit: netperf-2.7.0

./autogen.sh
# So strange, configure writes the spec file
./configure
sed -i -e 's|BuildRequires: texinfo, texinfo-tex||g' netperf.spec
rpmbuild --build-in-place -bb netperf.spec
