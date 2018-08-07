#!/bin/bash

# Unprivileged access to RDMA devices
mkdir -p /dev/infiniband
chmod g+rw -R /dev/infiniband/
chgrp 1000 -R /dev/infiniband/

# Switching /sys to ro informs systemd it is running in a container and that
# it should disable certain operations, like starting udev.
export container=docker
mount -o remount,ro /sys

exec /sbin/init $*
