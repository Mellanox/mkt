#!/bin/bash
# ---
# git_url: http://l-gerrit.mtl.labs.mlnx:8080/simx
# git_commit: 1af4eec8ea187a4727bf1821ffcdab0c276a7d3b

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
