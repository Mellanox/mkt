#!/bin/bash
# ---
# git_url: ssh://git-nbu.nvidia.com:12023/simx/simx-qemu
# git_commit:  0eb16838d915b191988f2e4bb3985aa84ea9bffa
# other_files:
#  - 0001-build-Don-t-install-files-that-we-are-not-interested.patch
#  - 0002-simx_configure-Overcome-dangling-pointer-compilation.patch
#  - 0003-simx-Fix-function-mismatch.patch

patch -p1 < /opt/0001-*.patch
patch -p1 < /opt/0002-*.patch
patch -p1 < /opt/0003-*.patch

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
