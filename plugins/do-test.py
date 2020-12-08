#!/usr/bin/env python3
# This is intended to be the entry for a docker container that has a bootable OS.
# It arranges to run the os under KVM with the docker filesystem as the rootfs,
# and can pass through pci devices to the KVM.

import argparse
import fnmatch
import os
import re
import shutil
import socket
import subprocess
import collections
import pickle
import base64
import multiprocessing
import shlex
import stat

# NOTES:
#   1. Get image from https://people.debian.org/~aurel32/qemu/amd64/debian_wheezy_amd64_standard.qcow2
#   2. Update Grub to see kernel images:
#      - nano /etc/default/grub, add GRUB_CMDLINE_LINUX_DEFAULT="debug earlyprintk=serial console=ttyS0"
#      - update-grub


cmd = ["/opt/simx/bin/qemu-system-x86_64", '-smp', 'cores=2', '-m', '1G', '-nographic',
        '-serial', 'mon:stdio', '-cpu', 'host', '-enable-kvm', '/images/artemp/src/kernel/Debian_check_qemu/debian_wheezy_amd64_standard.qcow2']

os.execvp(cmd[0], cmd)

