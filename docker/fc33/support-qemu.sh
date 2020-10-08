#!/bin/bash
# ---
# git_url: git@github.com:artpol84/qemu.git
# bkp_git_commit: 0261e73224a48e99b2dabb065437ae21b3e08944
# git_commit: 16d97a001da
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
./configure \
        --prefix=/opt/qemu-sr \
        --disable-strip \
        --disable-qom-cast-debug \
        --extra-ldflags="-pie -Wl,-z,relro -Wl,-z,now" \
        --extra-cflags="-fPIE -DPIE" \
        --enable-trace-backends=simple,dtrace \
        --with-trace-file=/var/log/traces \
        --enable-werror \
        --disable-xen \
        --disable-virtfs \
        --enable-kvm \
        --enable-libusb \
        --enable-spice \
        --enable-seccomp \
        --disable-fdt \
        --disable-docs \
        --disable-sdl \
        --disable-debug-tcg \
        --disable-sparse \
        --disable-brlapi \
        --disable-vde \
        --disable-curses \
        --disable-curl \
        --enable-vnc-sasl \
        --enable-linux-aio \
        --enable-lzo \
        --enable-snappy \
        --enable-usb-redir \
        --enable-vnc-png \
        --disable-vnc-jpeg \
        --disable-vhost-scsi \
        --target-list=x86_64-softmmu \
        --block-drv-rw-whitelist=qcow2,raw,file,host_device,blkdebug,nbd,iscsi,gluster,rbd \
        --block-drv-ro-whitelist=vmdk,vhdx,vpc \
        --enable-debug-info \


#        --enable-debug

#        --audio-drv-list=alsa \
#        --enable-rbd \
#        --disable-bluez \
#        --enable-glusterfs \

./scripts/git-submodule.sh update

make %{?_smp_mflags}

#%install
make DESTDIR=%{buildroot} install

%files
/opt/qemu-sr/*
EOF

rpmbuild --build-in-place -bb mlx-qemu.spec
