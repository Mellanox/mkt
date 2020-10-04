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
        "-net": [ "nic,model=virtio,macaddr=52:54:8a:aa:09:f5", "user,hostfwd=tcp::1807-:24" ],
        "-netdev": set(),
        "-device": ["virtio-rng-pci", "virtio-balloon-pci"],
        "-fsdev": [],

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
    parser.add_argument(
        '--sr',
        action="store_true",
        default=False,
        help="Request Suspendable QEMU")
    parser.add_argument(
        '--sr_qemu',
        action="store_true",
        default=False,
        help="Request a custom SR-enabled QEMU")
    parser.add_argument(
        '--mtty',
        action="store_true",
        default=False,
        help="Setup MTTY demo driver")
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

def l2_fix_l1_mounts(path):
    print ("Remove unneeded mounts")
    cmd = "/bin/rm -f " + path + "/etc/systemd/system/local-fs.target.{wants,requires}/*"
    print (" -> " + cmd)
    subprocess.run(cmd, shell=True, check=True)
    cmd = "/bin/rm -f " + path + "/etc/systemd/system/custom.target.wants/sriov\\\\x2dvfs.service"
    print (" -> " + cmd)
    subprocess.run(cmd, shell=True, check=True)
    cmd = "/bin/rm -f " + path + "/etc/systemd/system/*mount"
    print (" -> " + cmd)
    subprocess.run(cmd, shell=True, check=True)

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
    bind_dirs = ["bin", "boot", "home", "lib", "lib64", "opt", "sbin", "usr", "images", "images/artemp/src/kernel/", "plugins" ] #"labhome", 
    for d in bind_dirs:
        subprocess.check_call(["mount", "--bind", "/" + d, path + "/" + d])

    print ("Recreate '/var' structure in " + path + "/var/")
    cmd = "cd /var; find . -type d -exec mkdir -p -- " + path + "/var/{} \;"
    subprocess.run(cmd, shell=True, check=True)

    print ("Copy '/etc' content to " + path + "/etc/")
    cmd = "cp -R /etc/* " + path + "/etc"
    subprocess.run(cmd, shell=True, check=True)

    l2_fix_l1_mounts(path)

    # Setup plan9 virtfs
    qemu_args["-fsdev"].append("local,id=host_fs,security_model=passthrough,path=%s" % (path))
    qemu_args["-device"].append("virtio-9p-pci,fsdev=host_fs,mount_tag=/dev/root")

def prepare_rootfs_sr(qemu_args, path, image_path):

    # Cleanup the mount directory
    print ("Unmount everything under " + path)
    clean_mounts(path)
    print ("qemu-nbd -d /dev/nbd0")
    subprocess.run("/opt/simx/bin/qemu-nbd -d /dev/nbd0", shell=True, check=True)

    if os.path.isdir(path):
        print ("Remove existing content of " + path)
        subprocess.check_call(["rm", "-Rf", path])

    print ("Create " + path)
    os.makedirs(path)


    # Prepare image
    # Ensure the directory is there
    subprocess.run("mkdir -p `dirname " + image_path +"`" , shell=True, check=True)

    subprocess.run("modprobe nbd max_part=8", shell=True, check=True)
    
    if not os.path.isfile(image_path):
        print ("Initialize image (one-time operation)")
        # Create image
        subprocess.run("/opt/simx/bin/qemu-img create -f qcow2 " + image_path + " 10G", shell=True, check=True)
        subprocess.run("/opt/simx/bin/qemu-nbd -c /dev/nbd0 " + image_path, shell=True, check=True)
        subprocess.run("mkfs.ext3 /dev/nbd0", shell=True, check=True)
        subprocess.run("mount /dev/nbd0 " + path, shell=True, check=True)

        # Populate the rootfs
        print ("Recreate '/' structure in " + path)
        cmd = "for i in `ls -1 /`; do mkdir -p " + path + "/$i; done"
        subprocess.run(cmd, shell=True, check=True)

        print ("Copy basic files to the rootfs")
        base_dirs = ["bin", "boot", "lib", "lib64", "opt", "sbin", "usr", "plugins", "var", "etc" ]
        for d in base_dirs:
            cmd = "cp -Rfa /" + d + "/* " + path + "/" + d + "/"
            print (" ->  " + cmd)
            subprocess.run(cmd, shell=True, check=True)
        print(" -> Done")

        l2_fix_l1_mounts(path)
        
    else:
        print ("Mount existing image " + image_path + " to " + path)
        subprocess.run("/opt/simx/bin/qemu-nbd -c /dev/nbd0 " + image_path, shell=True, check=True)
        subprocess.run("mount /dev/nbd0 " + path, shell=True, check=True)

    print ("Update volatile files in the rootfs")
    update_dirs = ["lib/modules", "plugins" ]
    for d in update_dirs:
        cmd = "/bin/rm -Rf " + path + "/" + d + "/*"
        print (" ->  " + cmd)
        subprocess.run(cmd, shell=True, check=True)
        cmd = "cp -Rfa /" + d + "/* " + path + "/" + d + "/"
        print (" ->  " + cmd)
        subprocess.run(cmd, shell=True, check=True)
    print(" -> Done")


    print ("umount " + path)
    subprocess.check_call(["umount", path ])
    print ("qemu-nbd -d /dev/nbd0")
    subprocess.run("/opt/simx/bin/qemu-nbd -d /dev/nbd0", shell=True, check=True)
    
    qemu_args["-drive"] = { "if=virtio,format=qcow2,file=" + image_path}

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

def set_kernel_nested(qemu_args, tree, want_sr):

    if (want_sr) :
        # To enable Suspend/Resume and live Migration
        subprocess.check_call(['modprobe', '-r', 'kvm_intel'])
        subprocess.check_call(['modprobe', 'kvm_intel', 'nested=0'])
        # Setup kernel args
        root_args = "root=/dev/vda rootfstype=ext3"
    else:
        root_args = "root=/dev/root rootfstype=9p rootflags=trans=virtio "

    qemu_args.update({
        "-kernel":
        os.path.join(tree, "arch/x86/boot/bzImage"),
        # to debug:  systemd.journald.forward_to_console=1 systemd.log_level=debug
        # Change and enable debug-shell.service to use /dev/console
        "-append":
        root_args +' rw ignore_loglevel earlyprintk=serial,ttyS0,115200 \
        console=hvc0 noibrs noibpb nopti nospectre_v2  nospectre_v1 l1tf=off nospec_store_bypass_disable no_stf_barrier \
        mds=off mitigations=off'
    })

def set_vfio_dev(qemu_args, devid):
    qemu_args["-device"].append("vfio-pci,host=" + devid)

def set_mtty(qargs):
    mtty_base="/sys/devices/virtual/mtty/mtty"
    mtty_create= mtty_base + "/mdev_supported_types/mtty-2/create"
    mtty_dev="/sys/bus/mdev/devices/83b8f4f2-509f-382f-3c1e-e6bfe0fa1001"
    if not os.path.isdir(mtty_dev):
        if not os.path.isdir(mtty_base):
            cmd="modprobe mtty"
            subprocess.run(cmd, shell=True, check=True)
        with open(mtty_create, "w") as F:
            F.write("83b8f4f2-509f-382f-3c1e-e6bfe0fa1001")
    qargs["-device"].append("vfio-pci,sysfsdev=" + mtty_dev)
