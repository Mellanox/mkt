#!/bin/bash
set -e

# Do not create BTRFS subvolumes, docker explodes if you do this.
sed --in-place -e 's/^\(v.*\)$/\#\1/g' /usr/lib/tmpfiles.d/var.conf

# Do not try and set quota on /home/ in case it is automounted, otherwise systemd explodes
rm /usr/lib/tmpfiles.d/home.conf

# usual lab password
sed --in-place -e 's|root:.*$|root:$6$JAo7JDUgBkI7XOOT$VEdT3RUDM9m1kKNxmc/jBby0Rv9cgYq7rfi6b5bKsecZAKNTQl0PZLEx2Z7v0XwxwXtuqgtufG4XYrBLiz59g/:17751:0:99999:7:::|g' /etc/shadow

# Some random stable host key
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCodLhpgsAw7KHHYuSnUrXtUBJxqdIjncQjcA/X3P4qAEZjq34x5CSKfcVxTJ2FoZrUsNZHhkjJmbJLp2We7nApFUN1t83EmuxpRS4mhNRU1mRKH0pvrzFVmACXzbdVuKIUdQ+Tht60ndEpg/B6+Ei7rWeAT3eoVSdir098w6E1J+PcpPnOIJ617XjDmvKtVV4KhQgFSRfnALlhAywjSpSk8s3YEnLuAGUl33HjAqcS0/Tb9Bbv/WMyauhluKUh5vsrVmpUBWm5FX+36SCv+AW+dEKHEF7cddT73ntgf1G0b3EbSmeky+Zmc+ikeUIrXXGLbuMJ75AgU3SjtzFMErf/ root@cbe2d0e5f74d' > /etc/ssh/ssh_host_rsa_key.pub
chmod 0600 /etc/ssh/ssh_host_rsa_key

# Use a sshd socket
cat <<EOF > /etc/systemd/system/sshd@.service
[Unit]
Description=OpenSSH per-connection server daemon
After=auditd.service
After=systemd-user-sessions.service
Wants=systemd-user-sessions.service

[Service]
ExecStart=-/usr/sbin/sshd -i -e
StandardInput=socket
StandardError=syslog
EOF
systemctl disable sshd.service

# Automatically start a console
cat <<EOF > /etc/systemd/system/shell-console.service
[Unit]
Description=Console Shell
DefaultDependencies=no
Conflicts=shutdown.target
Conflicts=rescue.service
Conflicts=syslog.socket
Before=shutdown.target

[Service]
Environment=HOME=/root
WorkingDirectory=-/root
ExecStart=-/bin/login -f root
Type=idle
StandardInput=tty-force
StandardOutput=inherit
StandardError=inherit
KillMode=process
IgnoreSIGPIPE=no
SendSIGHUP=yes
EOF

# Setup ulimits good for rdma
cat <<EOF > /etc/security/limits.d/local-rdma.conf
* hard memlock unlimited
* soft memlock unlimited
EOF

cat <<EOF > /etc/fstab
EOF

cat <<EOF > /etc/locale.conf
LANG="en_CA.UTF-8"
EOF

cat <<EOF > /etc/sysctl.d/hugepages.conf
vm.nr_hugepages=2
EOF

rpm -U --force /opt/rpms/*.rpm
