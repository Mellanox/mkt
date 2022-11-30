#!/bin/bash
# ---
# git_url: http://l-gerrit.mtl.labs.mlnx:8080/simx-qemu
# git_commit: 4997d5d493704d8e0afd6d09925adaf7938c518e
# other_files:
#  - 0001-build-Don-t-install-files-that-we-are-not-interested.patch

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
