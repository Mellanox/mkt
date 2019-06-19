#!/bin/bash
# ---
# git_url: http://webdev01.mtl.labs.mlnx:8080/git/simx.git
# git_commit: dd77dfb88a7f08157819240cb7c99b1f82f57b21

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

#%install
make DESTDIR=%{buildroot} install
mkdir -p %{buildroot}/etc/qemu-kvm/
ln -s /etc/qemu/bridge.conf %{buildroot}/etc/qemu-kvm/bridge.conf

%files
/opt/simx/*
/etc/qemu-kvm/bridge.conf
EOF

rpmbuild --build-in-place -bb mlx-simx.spec
