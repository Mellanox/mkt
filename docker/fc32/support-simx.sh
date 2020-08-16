#!/bin/bash
# ---
# git_url: http://webdev01.mtl.labs.mlnx:8080/git/simx.git
# git_commit: e39b67e660f78fd2de6363ecf563f6cc651188ed
# other_files:
#   - 0001-mlx5-infra-Added-support-to-RMP-to-work-with-ODP.patch
#   - 0002-mlx5-infra-Added-support-to-RDMA-READ-with-ODP.patch
#   - 0003-mlx5-infra-Added-support-to-ODP-in-UD.patch

patch -p1 < /opt/0001*.patch
patch -p1 < /opt/0002*.patch
patch -p1 < /opt/0003*.patch

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
./mlnx_infra/config.status.mlnx --target=x86 --prefix=/opt/simx
make %{?_smp_mflags}
make %{?_smp_mflags} -C mellanox/

#%install
make DESTDIR=%{buildroot} install
mkdir -p %{buildroot}/etc/qemu-kvm/
ln -s /etc/qemu/bridge.conf %{buildroot}/etc/qemu-kvm/bridge.conf
mkdir -p %{buildroot}/opt/simx/lib/
cp mellanox/libml*.so %{buildroot}/opt/simx/lib/

%files
/opt/simx/*
/etc/qemu-kvm/bridge.conf
EOF

rpmbuild --build-in-place -bb mlx-simx.spec
