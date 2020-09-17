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

# =========================================================
# NOTE: A copy/paste from do-kvm. Can go to lib
# =========================================================
def get_mtab():
    paths = {}
    with open("/proc/mounts", "rt") as F:
        for I in F:
            I = I.split()
            paths[I[1]] = I
    return paths

def get_ip_tag(res, tag):
    """Given a string with 'tag XXX' return 'XXX'"""
    lst = res.split()
    for idx, I in enumerate(lst):
        if I == tag:
            return lst[idx + 1]
    raise ValueError("No tag %r in %r" % (tag, res))


# NOTE: copied from do-kvm
def set_console(qemu_args):
    """stdin is multiplexed onto three things, the monitor, the serial port and
    hvc0 (virtconsole).  The boot starts showing the serial port and switches
    to hvc0 when the first output happens there. 'Ctrl-a c' will rotate
    through the muxes."""
    qemu_args.update({
        "-chardev": "stdio,id=stdio,mux=on,signal=off",
        "-mon": "chardev=stdio"
    })
    qemu_args["-device"].extend([
        "isa-serial,chardev=stdio", "virtio-serial-pci",
        "virtconsole,chardev=stdio"
    ])


def set_kernel_rpm(quemu_args, src):
    """Setup a kernel from a compiled kernel RPM"""
    print("Extracting RPM %r" % (src))
    fns = subprocess.check_output(
        ["rpm2cpio %s | cpio -idmv" % (shlex.quote(src))], shell=True, cwd="/", stderr=subprocess.STDOUT)
    for ln in fns.splitlines():
        if ln.startswith(b"./boot/vmlinuz-"):
            vmlinuz = ln[1:]
            break
    else:
        raise ValueError("Could not find vmlinux in the RPM %r" % (src))

    qemu_args.update({
        "-kernel":
        vmlinuz,
        "-append":
        'root=/dev/root rw ignore_loglevel rootfstype=9p rootflags=trans=virtio earlyprintk=serial,ttyS0,115200 console=hvc0'
    })


# =========================================================
# NOTE: New functions derived from those in do-kvm
# =========================================================

# Based create_mount
def clean_mounts(dfn):
    mtab = {I for I in get_mtab().keys() if I.startswith(dfn)}
    while mtab:
        for I in sorted(mtab, reverse=True):
            subprocess.check_call(["umount", I])
        mtab = {I for I in get_mtab().keys() if I.startswith(dfn)}

def set_def_qemu_args():
    qemu_args = {
        "-enable-kvm": None,
        # Escape sequence is ctrl-a c q
        "-nographic": None,
        "-machine": "q35",
        "-cpu": "host",
        "-vga": "none",
        "-no-reboot": None,
        "-nodefaults": None,
        "-m": "1G", #str( int(float(args.mem) / 2)),
        "-net": [],
        "-netdev": set(),
        "-device": ["virtio-rng-pci", "virtio-balloon-pci"],

        # Newer FC28 qemu has a version of SeaBIOS with serial console (1.11)
        # support that clears the console and disables line wrapping, see
        # https://mail.coreboot.org/pipermail/seabios/2017-September/011792.html
        #
        # This is really annoying, disable it by telling SeaBIOS to use a bogus
        # serial port for its output.
        "-fw_cfg": ["etc/sercon-port,string=2"],
        "-smp": "%s" % int( multiprocessing.cpu_count() / 2)
    }
    return qemu_args

# =========================================================
# Specific to do-nested-kvm
# =========================================================


# Note: interacts with the upper-level do-kvm.py 
def input_from_pickle():
    pickle_path = "/etc/mkt_settings.pickle"
    with open(pickle_path, "rb") as F:
        p = pickle.load(F)

    parser = argparse.ArgumentParser(
        description='Launch QEMU using a copy of the the filesystem from the container')
    args = parser.parse_args()

    print (p)
    args.kernel = p.get("kernel", None)
    args.kernel_rpm = p.get("kernel_rpm", None)
    args.simx = p.get("simx", False)
    args.boot_script = p.get("boot_script", None)
    args.custom_qemu = p.get("custom_qemu", None)
    args.mem = p.get("mem", "500M")
    print (args)
    return args

def prepare_rootfs(qemu_args, path):

    print ("Unmount everything under " + path)
    clean_mounts(path)

    if os.path.isdir(path):
        print ("Remove existing content of " + path)
        subprocess.check_call(["rm", "-Rf", path])

    print ("Create " + path)
    os.makedirs(path)
    
    print ("Recreate '/' structure in " + path)
    cmd = "for i in `ls -1 /`; do mkdir " + path + "/$i; done"
    subprocess.run(cmd, shell=True, check=True)

    print ("Bind static portions of the rootfs")
    bind_dirs = ["bin", "boot", "etc", "home", "lib", "lib64", "opt", "sbin", "usr", "images", "plugins" ] #"labhome", 
    for d in bind_dirs:
        subprocess.check_call(["mount", "--bind", "/" + d, path + "/" + d])

    print ("Recreate '/var' structure in " + path + "/var/")
    cmd = "cd /var; find . -type d -exec mkdir -p -- " + path + "/var/{} \;"
    subprocess.run(cmd, shell=True, check=True)

    # Setup plan9 virtfs
    qemu_args["-fsdev"] = {
        "local,id=host_fs,security_model=passthrough,path=%s" % (path)
    }
    qemu_args["-device"].append(
        "virtio-9p-pci,fsdev=host_fs,mount_tag=/dev/root")

def set_simx_nested(qemu_args):
    # Override current SimX config
    subprocess.check_call(['mount', '-t', 'tmpfs', '-o', 'size=2048', 'tmpfs', '/opt/simx/cfg/'])
    
    # Dummy config file
    with open('/opt/simx/cfg/simx-qemu.cfg', 'a+') as f:
        f.write('[logger]\n')
        f.write('log_file_redirection = /logs/simx-qemu.log\n')
        f.write('[General Device Capabilities]\n')
        f.write('driver_version = false\n')
        f.write('query_driver_version = false\n')

def set_kernel_nested(qemu_args, tree):
    qemu_args.update({
        "-kernel":
        os.path.join(tree, "arch/x86/boot/bzImage"),
        # to debug:  systemd.journald.forward_to_console=1 systemd.log_level=debug
        # Change and enable debug-shell.service to use /dev/console
        "-append":
        'root=/dev/root rw ignore_loglevel rootfstype=9p rootflags=trans=virtio earlyprintk=serial,ttyS0,115200 \
 console=hvc0 noibrs noibpb nopti nospectre_v2  nospectre_v1 l1tf=off nospec_store_bypass_disable no_stf_barrier \
 mds=off mitigations=off'
    })

def set_vfio_dev(qemu_args, devid):
    qemu_args["-device"].append("vfio-pci,host=" + devid)
