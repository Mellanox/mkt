#!/bin/bash
# ---
# git_url: http://l-gerrit.mtl.labs.mlnx:8080/Linux_drivers_verification/pypacket
# git_commit: 31ad42d2496a8cf24e6f655435af43870d48ca6f

cat <<EOF > pypacket.spec
%global srcname pypacket
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
%{python2_sitelib}/*
EOF

rpmbuild --build-in-place -bb pypacket.spec
