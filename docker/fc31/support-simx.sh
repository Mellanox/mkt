#!/bin/bash
# ---
# git_url: http://webdev01.mtl.labs.mlnx:8080/git/simx.git
# git_commit: 21f3200268a84a0d104c0ac6453f6304aad58d35
# other_files:
#  - 0001-mlnx_infra-Disable-Wnonull-check-to-compile-on-FC31.patch
#  - 0002-keyamp-Make-compatible-with-python-3.patch

patch -p1 < /opt/0001-mlnx_infra-Disable-Wnonull-check-to-compile-on-FC31.patch
patch -p1 < /opt/0002-keyamp-Make-compatible-with-python-3.patch

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
