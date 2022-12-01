#!/bin/bash
# ---
# git_url: http://l-gerrit.mtl.labs.mlnx:8080/simx
# git_commit: 3cf48529796832dbf741bb5f283261690d624066

cat <<EOF > mlx-simx.spec
%global debug_package %{nil}

Name:           mlx-simx
Version:        1
Release:        1%{?dist}
Summary:	Mellanox simx enabled qemu
License:        Proprietary

%description
From simx.git

%build
SIMX_PROJECT=mlx5 make %{?_smp_mflags} -C mellanox

%install
mkdir -p %{buildroot}/opt/simx/lib/
cp mellanox/libml*.so %{buildroot}/opt/simx/lib/

%files
/opt/simx/*
EOF

rpmbuild --build-in-place -bb mlx-simx.spec
