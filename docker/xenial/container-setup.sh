#!/bin/bash
set -e

# sshd on an alternate port
cat <<EOF > /etc/systemd/system/sshd.socket
[Socket]
ListenStream=23
Accept=yes

[Install]
WantedBy=sockets.target
EOF
systemctl enable sshd.socket

# Disable nfs services
systemctl disable rpcbind.service run-rpc_pipefs.mount auth-rpcgss-module.service rpc-gssd.service rpc-svcgssd.service nfs-client.target

# Special target for booting everything needed for the container mode
cat <<EOF > /etc/systemd/system/container.target
[Unit]
Description=Containerized system
Requires=basic.target remote-fs.target systemd-user-sessions.service shell-console.service
Conflicts=rescue.service rescue.target
After=basic.target remote-fs.target systemd-user-sessions.service rescue.service rescue.target
AllowIsolate=yes
EOF
