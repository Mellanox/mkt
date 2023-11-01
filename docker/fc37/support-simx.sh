#!/bin/bash
# ---
# git_url: ssh://git-nbu.nvidia.com:12023/simx/simx
# git_commit: 774a6a135a4738a1abb6f23063c2814c7fa6e7df

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
