#!/bin/bash
# ---
# git_url: http://l-gerrit.mtl.labs.mlnx:8080/simx
# git_commit: 070998838203c06a760321fae6bd0fe8d7eaaa96
# other_files:
#  - 0001-build-Don-t-install-files-that-we-are-not-interested.patch
#  - 0002-Revert-9p-init_in_iov_from_pdu-can-truncate-the-size.patch
#  - 0003-simx-array-overflow.patch

patch -p1 < /opt/0001-build-Don-t-install-files-that-we-are-not-interested.patch
patch -p1 < /opt/0002-Revert-9p-init_in_iov_from_pdu-can-truncate-the-size.patch
patch -p1 < /opt/0003-simx-array-overflow.patch
sed -ie 's/--enable-werror//g' mlnx_infra/config.status.mlnx
sed -ie 's/-Werror//g' mellanox/Makefile

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
