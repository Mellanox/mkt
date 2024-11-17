#!/bin/bash
# ---
# git_url: /home/leonro/src/simx
# git_commit: 3c8ce7f00882ad2f37edfb28e78cd81a71d8002f
# other_files:
#  - 0001-mlx5-Fix-wrong-format-compilation-errors.patch

patch -p1 < /opt/0001-*.patch

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
