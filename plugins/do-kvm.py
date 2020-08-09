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

VM_Addr = collections.namedtuple("VM_Addr", "hostname ip mac")


def get_mtab():
    paths = {}
    with open("/proc/mounts", "rt") as F:
        for I in F:
            I = I.split()
            paths[I[1]] = I
    return paths


def create_mount(dfn):
    """Create a safe mount point and unmount everything under the directory"""
    if not os.path.isdir(dfn):
        os.makedirs(dfn)
        return

    mtab = {I for I in get_mtab().keys() if I.startswith(dfn)}
    while mtab:
        for I in sorted(mtab, reverse=True):
            subprocess.check_call(["umount", I])
        mtab = {I for I in get_mtab().keys() if I.startswith(dfn)}


def get_ip_tag(res, tag):
    """Given a string with 'tag XXX' return 'XXX'"""
    lst = res.split()
    for idx, I in enumerate(lst):
        if I == tag:
            return lst[idx + 1]
    raise ValueError("No tag %r in %r" % (tag, res))


def remove_mounts():
    """Get rid of the bind mounts over files that docker creates. It causes problems
    for the kvm via plan9 fs"""
    for I in get_mtab().keys():
        if not os.path.isfile(I):
            continue

        shutil.copy2(I, I + ".tmp")
        subprocess.check_call(["umount", I])
        os.rename(I + ".tmp", I)


def is_passable_mount(v):
    if v[2] == "nfs" or v[2] == "nfs4":
        return True
    if not v[0].startswith("/"):
        return False
    if v[1] == "/lab_tools":
        return False
    return True


def create_unit(unescaped_name, ext, links, text):
    unit = b"%s.%s" % (subprocess.check_output(
        ["systemd-escape", "--path", unescaped_name]).strip(), ext.encode())
    srv = os.path.join(b"/etc/systemd/system", unit)
    with open(srv, "w") as F:
        F.write(text)
    for I in links:
        ldfn = os.path.join(b"/etc/systemd/system/", I.encode())
        os.makedirs(ldfn, exist_ok=True)
        try:
            os.symlink(srv, os.path.join(ldfn, unit))
        except FileExistsError:
            pass


def setup_fs():
    """Prepare the root filesystem for KVM under /mnt/self - this is simply our /
    without all the virtual filesystems docker creates"""
    # Mount / into /mnt/self to get rid of all virtual filesystems
    mnt = "/mnt/self"
    create_mount(mnt)
    subprocess.check_call(["mount", "--bind", "/", mnt])

    # Setup plan9 virtfs
    qemu_args["-fsdev"] = {
        "local,id=host_fs,security_model=passthrough,path=%s" % (mnt)
    }
    qemu_args["-device"].append(
        "virtio-9p-pci,fsdev=host_fs,mount_tag=/dev/root")

    # Copy over local bind mounts, eg from docker -v
    cnt = 0
    for dfn, v in get_mtab().items():
        if not is_passable_mount(v):
            continue

        qemu_args["-fsdev"].add(
            "local,id=host_bind_fs%u,security_model=passthrough,path=%s" %
            (cnt, dfn))
        qemu_args["-device"].append(
            "virtio-9p-pci,fsdev=host_bind_fs%u,mount_tag=bind%u" % (cnt, cnt))

        create_unit(
            dfn, "mount", ["local-fs.target.wants"], """
[Unit]
Description=KVM mount {dfn}

[Mount]
What=bind{cnt:d}
Where={dfn}
Type=9p

[Install]
WantedBy=local-fs.target
""".format(cnt=cnt, dfn=dfn))

        create_unit(
            dfn, "automount", ["local-fs.target.requires"], """
[Unit]
Description=kvm auto mount {dfn}
Before=local-fs.target
Before=systemd-modules-load.service
Before=systemd-udevd.service

[Automount]
Where={dfn}
""".format(cnt=cnt, dfn=dfn))

        cnt = cnt + 1

def setup_login_script(args):
    """Create systemd unit to run custom user script right before login"""
    create_unit(
        "boot-script", "service", ["getty.target.wants"], """
[Service]
User={user}
Group={group}
ExecStart={script}
Type=oneshot
[Unit]
Description=Login script {script}
Wants=serial-getty@hvc0.service
After=serial-getty@hvc0.service

[Install]
WantedBy=getty.target
""".format(user=args.user, group=args.group, script=args.boot_script))

def terminal_size():
    import fcntl, termios, struct
    th, tw, hp, wp = struct.unpack(
        'HHHH',
        fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))
    return tw, th


def set_console():
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


def set_kernel(tree):
    """Use a compiled kernel tree as the boot kernel. This directly boots the
    bzimage in that tree and configures the KVM root filesystem to have a
    /lib/modules directory with symlinks back to the source tree. /boot/ is
    also setup in the usual way with symlinks."""
    bzimage = os.path.join(tree, "arch/x86/boot/bzImage")
    ver = get_ip_tag(
        subprocess.check_output(["file", bzimage]).decode(), "version")

    mdir = "/lib/modules/%s" % (ver)
    if os.path.isdir(mdir):
        shutil.rmtree(mdir)
    os.makedirs(mdir)

    files = subprocess.check_output([
        "find", tree, "-name", "modules.builtin", "-or", "-name",
        "modules.order", "-or", "-name", "*.ko"
    ]).split()
    files = [I.decode() for I in files]

    # Do not want to run 'make modules_install' so make these by hand..
    with open(os.path.join(mdir, "modules.builtin"), "wt") as out:
        for I in files:
            if I.endswith("modules.builtin"):
                with open(I) as F:
                    out.write(F.read())

    with open(os.path.join(mdir, "modules.order"), "wt") as out:
        for I in files:
            if I.endswith("modules.builtin"):
                with open(I) as F:
                    out.write(F.read())

    # Symlink modules
    mdir = os.path.join(mdir, "modules")
    if not os.path.isdir(mdir):
        os.makedirs(mdir)
    fn_info = {}
    for I in files:
        if I.endswith(".ko"):
            bn = os.path.basename(I)
            os.symlink(I, os.path.join(mdir, bn))
            st = os.stat(I)
            fn_info[bn] = {"size": st[stat.ST_SIZE],
                           "mtime": st[stat.ST_MTIME]}
    with open(os.path.join(mdir, "mkt_module_data.pickle"), "wb") as out:
        pickle.dump(fn_info, out)

    if os.path.isdir("/boot"):
        shutil.rmtree("/boot")
    os.makedirs("/boot")

    os.symlink(os.path.join(tree, "System.map"), "/boot/System.map-%s" % (ver))
    os.symlink(os.path.join(tree, ".config"), "/boot/config-%s" % (ver))
    os.symlink(bzimage, "/boot/vmlinuz-%s" % (ver))

    subprocess.check_call(["depmod", "-a", ver])

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


def set_kernel_rpm(src):
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

def set_custom_qemu(tree):
    """Overwrite installed QEMU variant with local version"""
    subprocess.check_call(['ln', '-f', '-s',
        tree + '/x86_64-softmmu/qemu-system-x86_64', '/opt/simx/bin/qemu-system-x86_64'])
    subprocess.check_call(['ln', '-f', '-s',
        tree + '/scsi/qemu-pr-helper', '/opt/simx/bin/qemu-pr-helper'])
    subprocess.check_call(['ln', '-f', '-s',
        tree + '/fsdev/virtfs-proxy-helper', '/opt/simx/bin/virtfs-proxy-helper'])
    subprocess.check_call(['ln', '-f', '-s',
        tree + '/qemu-bridge-helper', '/opt/simx/libexec/qemu-bridge-helper'])
    subprocess.check_call(['ln', '-f', '-s',
        tree + '/mellanox/libmlx.so', '/opt/simx/lib/libmlx.so'])

def set_bridge_network(args):
    """If a 'br0' is present then we can setup normal bridge networking"""
    qemu_args["-netdev"].add("bridge,br=br0,id=net0")
    qemu_args["-device"].append("virtio-net,netdev=net0,mac=" +
                                args.vm_addr.mac)


def set_loop_network(args):
    """Simple network that forwards our localhost port 4444 to the kvm's ssh
    port"""
    print(
        "No br0 bridge found, using NAT networking, connected to port localhost:4444 for ssh"
    )
    qemu_args["-net"].extend([
        "nic,model=virtio,macaddr=%s" % (args.vm_addr.mac),
        "user,hostfwd=tcp:127.0.0.1:4444-:22"
    ])

def set_simx_log():
    """Prepare simx log file."""

    subprocess.check_call(['mkdir', '-p', '/opt/simx/cfg/'])
    with open('/opt/simx/cfg/simx-qemu.cfg', 'a+') as f:
         f.write('[logger]\n')
         f.write('log_file_redirection = /logs/simx-qemu.log\n')
def set_sriov_vfs(args, idx, mode):
    qemu_args["-device"].append('pcie-root-port,pref64-reserve=500M,slot=%d,id=pcie_port.%d' %(idx-1, idx))
    # TODO: Configure SRIOV for more than one card
    if mode == "ib":
        sriov_device="infiniband/`ls -1 /sys/class/infiniband/ | head -1`"
    else:
        sriov_device='net/eth1'

    create_unit(
                "sriov-vfs", "service", ["custom.target.wants"], """
[Unit]
Before=
Requires=multi-user.target
After=multi-user.target
AllowIsolate=yes
[Service]
Type=oneshot
RemainAfterExit=false
ExecStart=/bin/bash -c \"echo {numb} > /sys/class/{device}/device/sriov_numvfs\"
[Install]
WantedBy=custom.target
""".format(numb=args.num_of_vfs, device=sriov_device))

def have_netdev(name):
    try:
        subprocess.check_output(
            ["ip", "link", "show", "dev", name], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return False;
    return True;

def set_simx_network(simx):
    """Setup options to start a simx card"""
    to_simx_device = { 'cx4' : 'connectx4',
                       'cx4lx' : 'connectx4lx',
                       'cx5' : 'connectx5',
                       'cx5ex' : 'connectx5_ex',
                       'cx6' : 'connectx6',
                       'cx6dx' : 'connectx6_dx',
                       'cx6lx' : 'connectx6_lx',
                       'cx7' : 'connectx7',
                       'cib' : 'connectib'
                       }
    subprocess.check_call(['mkdir', '-p', '/opt/simx/cfg/'])
    have_virbr = have_netdev("virbr0")

    with open('/opt/simx/cfg/simx-qemu.cfg', 'a+') as f:
        f.write('[General Device Capabilities]\n')
        f.write('driver_version = false\n')
        f.write('query_driver_version = false\n')
        f.write('num_ports = %s\n' % (args.num_ports))

        idx = 1
        eth_sriov = False
        for target in simx:
            dev = target.split('-')[0]
            mode = target.split('-')[1]
            devargs = to_simx_device[dev]
            f.write('[device_%d]\n' % (idx - 1))
            if mode == 'ib':
                f.write('port_type = 0x0\n')
            else:
                # Ethernet
                f.write('port_type = 0x1\n')

            if args.num_of_vfs:
                devargs += ',bus=pcie_port.%d' %(idx)
                set_sriov_vfs(args, idx, mode)

            if have_virbr:
                qemu_args["-netdev"].add("bridge,br=virbr0,id=net%d" %(idx))
                devargs += ',netdev=net%d' %(idx)

            qemu_args["-device"].append(devargs)
            idx = idx + 1

        if args.num_of_vfs:
            f.write('[adapter]\n')
            f.write('num_of_function = %s\n' % (args.num_of_vfs))

def set_virt_devices(args):
    qemu_args["-append"] += " modules_load=rdma_rxe";

def set_vfio(args):
    """Pass a VFIO owned PCI device through to the guest"""
    for bdf in args.vfio:
        qemu_args["-device"].append("vfio-pci,host=%s" % (bdf))


def write_once(fn, val):
    with open(fn) as F:
        tmp = F.read()
        if val in tmp:
            return
    with open(fn, "at") as F:
        F.write(val)


def setup_console(user):
    """Configure the tty settings for the console inside kvm to match the settings
    in docker. This doesn't track dynamically, eg you cannot resize the
    terminal window and have things work, but it does track once at boot. This
    avoids a bug in FC28 agetty that does not configure the console properly
    resulting in passwd prompts not working. Unfortunately we can't invoke
    login here, for some reason it erases the terminal geometry settings."""
    os.makedirs(
        "/etc/systemd/system/serial-getty@hvc0.service.d", exist_ok=True)
    stty_config = subprocess.check_output(["stty", "-g"])
    stty_config = stty_config.decode().strip()
    geom = terminal_size()
    with open("/etc/systemd/system/serial-getty@hvc0.service.d/override.conf",
              "wt") as F:
        F.write("""[Service]
TTYPath=/dev/%I
UtmpMode=login
StandardInput=tty-force
StandardOutput=tty
StandardError=tty
Environment=TERM={term}
ExecStart=
ExecStart=-/bin/bash -c "/usr/bin/stty {stty_config} && /usr/bin/stty cols {cols} rows {rows} && exec /usr/bin/su --shell=/bin/bash -l {user}"
""".format(
            user=user,
            stty_config=stty_config,
            cols=geom[0],
            rows=geom[1],
            term=os.environ.get("TERM", "xterm"),
        ))

def setup_gdbserver(args):
    if args.gdbserver:
        qemu_args['-gdb'] = 'tcp::%d' % args.gdbserver

def setup_from_pickle(args, pickle_params):
    """The script that invokes docker passes in some more detailed parameters
    about the environment in a pickle and we adjust the configuration
    accordingly"""
    p = pickle.loads(base64.b64decode(pickle_params))
    write_once("/etc/passwd",
               "{user}:x:{uid}:{gid}:,,,:{home}:{shell}\n".format(**p))
    write_once("/etc/shadow", "{user}:x:17486:0:99999:7:::\n".format(**p))
    write_once("/etc/group", "{group}:x:{gid}:\n".format(**p))
    write_once("/etc/sudoers", "{user} ALL=(ALL) NOPASSWD:ALL\n".format(**p))

    setup_console(p["user"])

    args.kernel = p.get("kernel", None)
    args.kernel_rpm = p.get("kernel_rpm", None)
    args.simx = p.get("simx", False)
    args.vfio = p.get("vfio", [])
    args.virt = p.get("virt", False)
    args.vm_addr = VM_Addr(**p["vm_addr"])
    args.mem = p["mem"]
    args.boot_script = p.get("boot_script", None)
    args.user = p["user"]
    args.group = p["group"]
    args.num_of_vfs = p.get("num_of_vfs", 0)
    args.custom_qemu = p.get("custom_qemu", None)
    args.gdbserver = p.get("gdbserver", None)
    args.num_ports = p.get("num_ports", 1)

parser = argparse.ArgumentParser(
    description='Launch kvm using the filesystem from the container')
args = parser.parse_args()

pickle_data = os.environ.get("KVM_PICKLE")
if pickle_data:
    setup_from_pickle(args, pickle_data)

qemu_args = {
    "-enable-kvm": None,
    # Escape sequence is ctrl-a c q
    "-nographic": None,
    "-machine": "q35",
    "-cpu": "host",
    "-vga": "none",
    "-no-reboot": None,
    "-nodefaults": None,
    "-m": args.mem,
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
    "-smp": "%s" % (multiprocessing.cpu_count())
}

remove_mounts()
set_console()
setup_fs()

if args.kernel_rpm:
    set_kernel_rpm(args.kernel_rpm)
else:
    set_kernel(args.kernel)

if args.custom_qemu:
    set_custom_qemu(args.custom_qemu)

if have_netdev("br0"):
    set_bridge_network(args)
else:
    set_loop_network(args)

set_vfio(args)
if args.virt:
    set_virt_devices(args)

cmd = ["/opt/simx/bin/qemu-system-x86_64"]
if args.simx:
    set_simx_log()
    set_simx_network(args.simx)

setup_gdbserver(args)

for k, v in sorted(qemu_args.items()):
    if isinstance(v, set) or isinstance(v, list):
        for I in v:
            cmd.append(k)
            cmd.append(I)
    else:
        cmd.append(k)
        if v:
            cmd.append(v)

if args.boot_script:
    setup_login_script(args)

with open('/logs/qemu.cmdline', 'w+') as f:
    f.write(" ".join(cmd))
os.execvp(cmd[0], cmd)
