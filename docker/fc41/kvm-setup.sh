#!/bin/bash
set -e

cp /etc/pam.d/sshd /etc/pam.d/sshd.original
cat <<EOF > /etc/pam.d/sshd
auth       required     pam_permit.so
EOF
cat /etc/pam.d/sshd.original >> /etc/pam.d/sshd
rm -rf /etc/pam.d/sshd.original

# sshd on the normal port
cat <<EOF > /etc/systemd/system/sshd.socket
[Socket]
ListenStream=22
Accept=yes

[Install]
WantedBy=sockets.target
EOF
systemctl enable sshd.socket

# Auto start a root console on the qemu console. Note that do-kvm adds an
# override, see setup_console()
systemctl enable serial-getty@hvc0.service

# Use eth0 for the ethernet name
ln -s /dev/null /etc/systemd/network/99-default.link

# Enable networkd
mkdir -p /etc/systemd/network
CNT=0
while [  $CNT -lt 10 ]; do
cat <<EOF > /etc/systemd/network/0$CNT-ib.network
[Match]
Name=ib$CNT
Type=infiniband

[Network]
Address=192.168.100.1$CNT/24
EOF
	let CNT=CNT+1
done

cat <<EOF > /etc/systemd/network/10-kvm.network
[Match]
Virtualization=kvm

[Network]
DHCP=yes

[DHCP]
ClientIdentifier=mac
UseMTU=true
UseDomains=true
EOF

systemctl enable systemd-networkd.service systemd-resolved.service

# Create MKT custom target to run command as last unit
cat <<EOF > /etc/systemd/system/custom.target
[Unit]
Description=MKT custom target
Requires=multi-user.target
After=multi-user.target
AllowIsolate=yes
EOF

mkdir -p /etc/systemd/system/custom.target.wants
# Set our scripts to be executed last
ln -sf /etc/systemd/system/custom.target /etc/systemd/system/default.target

# Do not use /var/log/ with journald, doesn't work with 9pfs
rm -rf /var/log/journal

# Disable unneeded stuff
systemctl disable dnf-makecache.timer
systemctl disable ldconfig.service
systemctl mask ldconfig.service
/sbin/ldconfig -X
systemctl disable systemd-hibernate-clear.service
systemctl disable systemd-pcrmachine.service
systemctl disable systemd-pstore.service
systemctl disable systemd-repart.service
systemctl mask systemd-repart.service
systemctl disable systemd-pcrmachine.service
systemctl mask systemd-pcrmachine.service
systemctl disable systemd-tpm2-setup-early.service
systemctl mask systemd-tpm2-setup-early.service
systemctl disable systemd-tpm2-setup.service
systemctl mask systemd-tpm2-setup.service
systemctl disable systemd-hibernate-clear.service
systemctl mask systemd-hibernate-clear.service

#sed -i -e 's/tty9/hvc0/g' /lib/systemd/system/debug-shell.service
#systemctl enable debug-shell.service

# Undo the systemd masking done for the container image
systemctl unmask systemd-logind.service systemd-remount-fs.service getty.target dev-hugepages.mount console-getty.service

# users can use RDMA
cat <<EOF > /etc/udev/rules.d/00-rdma.rules
KERNEL=="umad[0-9]*", GROUP="1000", MODE="0660"
KERNEL=="issm[0-9]*", GROUP="1000" MODE="0660"
KERNEL=="uverbs[0-9]*", GROUP="1000"
KERNEL=="rdma_ucm", GROUP="1000"
EOF

echo allow br0 >> /etc/qemu/bridge.conf

# Avoid writing hwdb.bin on boot
systemd-hwdb update --usr
rm -f /etc/udev/hwdb.bin
# Allow to regular users to run ping
chmod a+s /usr/bin/ping
