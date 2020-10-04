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

import mkt_utils as mkt

args = mkt.input_from_pickle()
qargs = mkt.set_def_qemu_args()
print (args)

if (args.sr):
    print ("Suspend/Resume capable execution requested")

if args.sr:
    mkt.prepare_rootfs_sr(qargs, "/mnt/self2", "/images/artemp/src/kernel/0nested_image/nested_image.qcow2")
else:
    mkt.prepare_rootfs(qargs, "/mnt/self2")

mkt.set_console(qargs)

mkt.set_kernel_nested(qargs, args.kernel, args.sr)

if (args.sr_qemu):
    cmd = ["/opt/qemu-sr/bin/qemu-system-x86_64"]
else:
    cmd = ["/opt/simx/bin/qemu-system-x86_64"]


mkt.set_simx_nested(qargs)

try:
    with open('/tmp/vfio.id', 'r') as f:
        t = f.read().strip()
        print ('VFIO: setup passthrough for %s' % (t))
        mkt.set_vfio_dev(qargs, t)
except Exception as error:
        print ('Skip VFIO passthrough setup')

for k, v in sorted(qargs.items()):
    if isinstance(v, set) or isinstance(v, list):
        for I in v:
            cmd.append(k)
            cmd.append(I)
    else:
        cmd.append(k)
        if v:
            cmd.append(v)

#cmd = ["/opt/simx/bin/qemu-system-x86_64", '-smp', 'cores=2', '-m', '1G', '-nographic',
#        '-serial', 'mon:stdio', '-cpu', 'host', '-enable-kvm', '/images/artemp/src/kernel/Debian_check_qemu/debian_wheezy_amd64_standard.qcow2']

print (cmd)
os.execvp(cmd[0], cmd)
