#!/bin/bash
# ---
# nfs_files:
#  /mswg/release/tools/a-me/a-me-1.0.119/python_libs/adb.py:
#    dest: /opt/src/
#  /mswg/release/tools/a-me/a-me-1.0.119/python_libs/cadb-2.7-64/cadb.so:
#    dest: /opt/src/

# This comes from http://l-gerrit.mtl.labs.mlnx:8080/tools/a-me but in a
# bizzare twist the above depends on mft's source code too.

# Hackity hack to get ditutils to build an extension module
cat <<EOF > dummy.c
int thingy(void) {return 0;}
EOF

cat <<EOF > setup.py
from distutils.core import setup, Extension

setup(name="adb",
      version="1.0.119",
      description="Mellanox AME tool",
      url="http://l-gerrit.mtl.labs.mlnx:8080/tools/a-me",
      ext_modules=[Extension('cadb', ['dummy.c'])],
      py_modules=["adb"],
)
EOF

cat <<EOF > adb.spec
%global srcname adb
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
cat ./cadb.so > %{buildroot}/%{python2_sitearch}/cadb.so

%files
%{python2_sitearch}/*
EOF

rpmbuild --build-in-place -bb adb.spec
