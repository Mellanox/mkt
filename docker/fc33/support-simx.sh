#!/bin/bash
# ---
# git_url: /global/home/users/artemp/scratch/SOFTWARE/simx.git
# git_commit: 022bedab1
# old_git_commit: 7032d67e5
# old_git_commit: 9f601e894e3ac74795a8990c0349ea36059004c9

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
cat ./mlnx_infra/config.status.mlnx | grep -v '\-\-disable\-tools' > ./mlnx_infra/config.status.mlnx.new
chmod +x ./mlnx_infra/config.status.mlnx.new
./mlnx_infra/config.status.mlnx.new --target=x86 --prefix=/opt/simx
make %{?_smp_mflags}
make %{?_smp_mflags} -C mellanox/

#%install
make DESTDIR=%{buildroot} install
mkdir -p %{buildroot}/etc/qemu-kvm/
ln -s /etc/qemu/bridge.conf %{buildroot}/etc/qemu-kvm/bridge.conf
mkdir -p %{buildroot}/opt/simx/lib/
cp mellanox/libml*.so %{buildroot}/opt/simx/lib/
cp ./mlnx_infra/bridge-{start,stop}.sh  %{buildroot}/opt/simx/bin/

%files
/opt/simx/*
/etc/qemu-kvm/bridge.conf
EOF

rpmbuild --build-in-place -bb mlx-simx.spec

cd /opt/
tar -czvf simx-src.tar.gz src