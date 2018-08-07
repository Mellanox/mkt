#!/bin/bash
set -e

# sshd on the normal port
cat <<EOF > /etc/systemd/system/sshd.socket
[Socket]
ListenStream=22
Accept=yes

[Install]
WantedBy=sockets.target
EOF
systemctl enable sshd.socket

# Auto start a root console on the qemu console, either ttyS0 or hvc0
# depending on the kernel command line parameter.
mkdir -p /etc/systemd/system/serial-getty\@ttyS0.service.d/
cat <<EOF > /etc/systemd/system/serial-getty\@ttyS0.service.d/override.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --keep-baud 115200,38400,9600 --autologin root --noclear %I xterm
EOF

mkdir -p /etc/systemd/system/serial-getty\@hvc0.service.d/
cat <<EOF > /etc/systemd/system/serial-getty\@hvc0.service.d/override.conf
[Service]
ExecStart=
ExecStart=-/sbin/agetty --keep-baud 115200,38400,9600 --autologin root --noclear %I xterm
EOF

# systemd-resolved starts way too late and Xenial doesn't have the dbus auto
# starter either. I guess this stuff is not supposed to work..
# rpc.gss would be Ok if we had localhost in /etc/hosts
mkdir -p /etc/systemd/system/rpc-gssd.service.d
cat <<EOF > /etc/systemd/system/rpc-gssd.service.d/10-resolver.conf
[Unit]
Requires=systemd-resolved.service
After=systemd-resolved.service
EOF

# Note, NFS fails randomly because of https://github.com/systemd/systemd/issues/2037

# Load modules for kvm
cat <<EOF > /etc/systemd/system/kvm-load-modules.service
[Unit]
Description=Load modules after NFS starts
After=network-online.target

[Service]
ExecStartPre=/bin/bash -c 'mkdir -p /run/modules-load.d && echo -e "ib_uverbs\nib_umad\nrdma_ucm\nib_ipoib" > /run/modules-load.d/rdma.conf'
ExecStart=/lib/systemd/systemd-modules-load

[Install]
WantedBy=multi-user.target
EOF
systemctl enable kvm-load-modules.service

# Use eth0 for the ethernet name
ln -s /dev/null /etc/systemd/network/99-default.link

# Enable networkd
mkdir -p /etc/systemd/network
cat <<EOF > /etc/systemd/network/00-kvm.network
[Match]
Virtualization=qemu

[Network]
DHCP=yes

[Link]
NamePolicy=

[DHCP]
ClientIdentifier=mac
UseMTU=true
UseDomains=true
EOF
# For some reason Xenial is missing the bus activation for systemd-resolved
systemctl enable systemd-networkd.service systemd-resolved.service

systemctl enable /usr/share/systemd/tmp.mount

# users can use RDMA
cat <<EOF > /etc/udev/rules.d/00-rdma.rules
KERNEL=="umad[0-9]*", GROUP="1000", MODE="0660"
KERNEL=="issm[0-9]*", GROUP="1000" MODE="0660"
KERNEL=="uverbs[0-9]*", GROUP="1000"
KERNEL=="rdma_ucm", GROUP="1000"
EOF
