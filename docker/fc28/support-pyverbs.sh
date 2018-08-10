#!/bin/bash
# ---
# git_url: git@github.com:Mellanox/Pyverbs.git
# git_commit: 2018.10.24
# image_files:
#   local_mkt/support_rdma_core:fc28:
#       dest: /opt/rdma-core/
#       files:
#          - /root/rpmbuild/RPMS/x86_64/*.rpm

rm -f /opt/rdma-core/*debug*.rpm
rpm -U /opt/rdma-core/lib*.rpm /opt/rdma-core/ibacm*.rpm /opt/rdma-core/rdma-core*.rpm

# FIXME: Sigh, fix this in pyverbs git
sed --in-place -e 's/0xffffL/0xffff/g' pyverbs/examples/tm_pingpong.py

cat <<EOF > pyverbs.spec
%global srcname pyverbs
%global debug_package %{nil}

Name:           python2-%{srcname}
Version:        1
Release:        1%{?dist}
Summary:        Python verbs
License:        Proprietary

BuildRequires:  python2-devel

%description
Python verbs

%{?python_provide:%python_provide python2-%{srcname}}

%prep
%autosetup -n %{srcname}-%{version}

%build
%py2_build

%install
%py2_install

%files
%{python2_sitearch}/*
EOF

rpmbuild --build-in-place -bb pyverbs.spec
