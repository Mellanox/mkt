#!/bin/bash
# ---
# git_url: http://l-gerrit.mtl.labs.mlnx:8080/Linux_drivers_verification/onetest
# git_commit: rel-00_05_0076
# image_files:
#   local_mkt/support_rdma_core:fc28:
#       dest: /opt/rdma-core/
#       files:
#          - /root/rpmbuild/RPMS/x86_64/*.rpm
#   local_mkt/support_pyverbs:fc28:
#       dest: /opt/rpms/
#       files:
#          - /root/rpmbuild/RPMS/x86_64/*.rpm
#   local_mkt/support_pypacket:fc28:
#       dest: /opt/rpms/
#       files:
#          - /root/rpmbuild/RPMS/x86_64/*.rpm
#   local_mkt/support_pcapy:fc28:
#       dest: /opt/rpms/
#       files:
#          - /root/rpmbuild/RPMS/x86_64/*.rpm

rm -f /opt/rdma-core/*debug*.rpm /opt/rpms/*debug*.rpm
rpm -U /opt/rdma-core/lib*.rpm /opt/rdma-core/ibacm*.rpm /opt/rdma-core/rdma-core*.rpm /opt/rpms/*.rpm

# FIXME: Sigh, fix this in the onetest git
find . -type f | xargs chmod a-x

cat <<EOF > ontest.spec
%global srcname onetest
%global debug_package %{nil}

Name:           python2-%{srcname}
Version:        1
Release:        1%{?dist}
Summary:        Mellanox Driver test
License:        Proprietary

Requires: python2-ipaddr
Requires: python2-netaddr
Requires: python2-netifaces
Requires: python2-paramiko
Requires: python2-pathlib2
Requires: python2-pcapy >= 0.11.1
Requires: python2-pypacket
Requires: python2-pyverbs
Requires: python2-pyyaml
# FIXME: Requires: python2-plumbum
Requires: PyQt4
# FIXME: python-redmine

BuildRequires: python2-pyverbs
BuildRequires: python2-devel

%description
Driver test

%{?python_provide:%python_provide python2-%{srcname}}

%prep
%autosetup -n %{srcname}-%{version}

%build
%py2_build

%install
%py2_install
PYTHONPATH=%{buildroot}/%{python2_sitearch} %{buildroot}/%{_bindir}/drivertest_gui.py --help

%files
%{python2_sitearch}/*
%{_bindir}/drivertest*.py
EOF

# FIXME: pythondistdeps does not work

rpmbuild --build-in-place -bb ontest.spec
