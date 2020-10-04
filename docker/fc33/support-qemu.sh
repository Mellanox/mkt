#!/bin/bash
# ---
# git_url: git@github.com:artpol84/qemu.git
# git_commit: 1b5064289df4aba221c8b3e0f27594b41921b704
# git_modules: yes

cat <<EOF > mlx-qemu.spec
%global debug_package %{nil}

Name:           mlx-qemu
Version:        1
Release:        1%{?dist}
Summary:	    QEMU with Suspend/Resume (SR) capability for VFIO
License:        Proprietary

%description


%build
ls
./configure \
    --prefix=/opt/qemu-sr \
    '--block-drv-ro-whitelist=vmdk,vhdx,vpc' \
	'--block-drv-rw-whitelist=qcow,qcow2,raw,file,host_device,nbd,iscsi,vvfat' \
	'--disable-brlapi' \
	'--disable-capstone' \
	'--disable-curl' \
	'--disable-curses' \
	'--disable-debug-tcg' \
	'--disable-docs' \
	'--disable-guest-agent' \
	'--disable-glusterfs' \
	'--disable-gtk' \
	'--disable-libusb' \
	'--disable-live-block-migration' \
	'--disable-nettle' \
	'--disable-qom-cast-debug' \
	'--disable-rdma' \
	'--disable-replication' \
	'--disable-sparse' \
	'--disable-smartcard' \
	'--disable-sdl' \
	'--disable-strip' \
	'--disable-tools' \
	'--disable-vde' \
	'--disable-vhost-scsi' \
	'--disable-vnc-jpeg' \
	'--disable-vnc-png' \
	'--disable-vnc-sasl' \
	'--disable-xen' \
	'--enable-fdt' \
	'--enable-kvm' \
	'--enable-linux-aio' \
	'--enable-seccomp' \
	'--enable-spice' \
	'--enable-trace-backend=dtrace' \
	'--enable-usb-redir' \
	'--enable-vnc' \

#	'--enable-virtfs' \

make %{?_smp_mflags}

#%install
make DESTDIR=%{buildroot} install

%files
/opt/qemu-sr/*
EOF

rpmbuild --build-in-place -bb mlx-qemu.spec
