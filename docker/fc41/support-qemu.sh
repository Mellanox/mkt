#!/bin/bash
# ---
# git_url: //home/leonro/src/simx-qemu
# git_commit: 30a8d7c6295e4843b68e8a6f3fea3fb57a116bef
# other_files:
#  - 0001-simx_configure-Enable-user-networking.patch

patch -p1 < /opt/0001-*.patch


cat <<EOF > mlx-qemu.spec
%global debug_package %{nil}

Name:           mlx-qemu
Version:        1
Release:        1%{?dist}
Summary:	Mellanox QEMU
License:        Proprietary

%description
From simx-qemu.git

%build
./simx_configure --target=x86 --prefix=/opt/simx --disable-seccomp
make %{?_smp_mflags}

%install
make DESTDIR=%{buildroot} install
mkdir -p %{buildroot}/etc/qemu-kvm/
ln -s /etc/qemu/bridge.conf %{buildroot}/etc/qemu-kvm/bridge.conf

%files
/opt/simx/*
/etc/qemu-kvm/bridge.conf
EOF

rpmbuild --build-in-place -bb mlx-qemu.spec
