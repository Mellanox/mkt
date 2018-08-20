#!/bin/bash

set -e

cd /opt/src/simx

git reset --hard 0bb8c6753fd8314071bce3fd70a49f5b51803fa1
git config --global user.email "leonro@mellanox.com"
git config --global user.name "Leon Romanovsky"
git am /root/00*.patch

# See ./mlnx_infra/config.status.mlnx
SIMX_GCC_FLAGS=
SIMX_EXTRA_FLAGS="-I/usr/include/libnl3/"
SIMX_EXTRA_LDFLAGS=
SIMX_EXTRA_COMPILATION_FLAGS='--enable-werror'

make clean

'./configure' \
${SIMX_GCC_FLAGS} \
${SIMX_EXTRA_COMPILATION_FLAGS} \
'--python=/usr/bin/python2' \
'--prefix=/opt/simx' \
'--libdir=/opt/simx/lib' \
'--interp-prefix=/opt/simx/qemu-%M' \
'--with-confsuffix=/qemu-kvm' \
'--sysconfdir=/opt/simx/etc' \
'--localstatedir=/opt/simx/var' \
'--libexecdir=//opt/simx/libexec' \
"--with-pkgversion=simx-qemu-system-${PKGVERSION}" \
'--disable-strip' \
'--disable-qom-cast-debug' \
"--extra-cflags=-Wundef -Wredundant-decls -Wunreachable-code -Wno-format ${SIMX_EXTRA_FLAGS}" \
"--extra-ldflags=${SIMX_EXTRA_LDFLAGS}" \
'--enable-trace-backend=dtrace' \
'--disable-xen' \
'--enable-virtfs' \
'--enable-kvm' \
'--enable-libusb' \
'--enable-spice' \
'--enable-seccomp' \
'--enable-fdt' \
'--disable-docs' \
'--disable-sdl' \
'--disable-debug-tcg' \
'--disable-sparse' \
'--disable-brlapi' \
'--disable-bluez' \
'--disable-vde' \
'--disable-curses' \
'--disable-curl' \
'--enable-vnc' \
'--disable-vnc-sasl' \
'--enable-linux-aio' \
'--enable-usb-redir' \
'--disable-vnc-png' \
'--disable-vnc-jpeg' \
'--disable-gtk' \
'--disable-vhost-scsi' \
'--disable-guest-agent' \
'--disable-glusterfs' \
'--block-drv-rw-whitelist=qcow,qcow2,raw,file,host_device,nbd,iscsi,vvfat' \
'--block-drv-ro-whitelist=vmdk,vhdx,vpc' \
'--disable-rdma' \
'--disable-tools' \
'--disable-capstone' \
'--target-list=x86_64-softmmu'

make -j`nproc`
make install
rm -rf /opt/src
mkdir -p /opt/simx/etc/qemu-kvm/
ln -s /etc/qemu/bridge.conf /opt/simx/etc/qemu-kvm/bridge.conf
