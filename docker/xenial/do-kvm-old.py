#!/usr/bin/env python
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

def get_fs_tab():
    prefixes = set();
    with open("/etc/fstab") as F:
        for I in F:
            if I.strip().startswith("#"):
                continue;
            prefixes.add(I.split()[1]);
    return prefixes;

def get_mtab():
    paths = set();
    with open("/proc/mounts") as F:
        for I in F:
            paths.add(I.split()[1]);
    return paths;

def create_mount(dfn):
    if not os.path.isdir(dfn):
        os.makedirs(dfn);
        return;

    mtab = {I for I in get_mtab() if I.startswith(dfn)};
    while mtab:
        for I in sorted(mtab,reverse=True):
            subprocess.check_call(["umount",I]);
        mtab = {I for I in get_mtab() if I.startswith(dfn)};

def get_ip_tag(res,tag):
    """Given a string with 'tag XXX' return 'XXX'"""
    lst = res.split();
    for idx,I in enumerate(lst):
        if I == tag:
            return lst[idx+1];
    raise ValueError("No tag %r in %r"%(tag,res));

def setup_mem():
    """Use 70% of system memory for the VM"""
    with open("/proc/meminfo") as F:
        for I in F:
            tag,_,value = I.partition(":")
            value = value.strip()
            if tag == "MemTotal":
                value = value.split();
                if value[1] == "kB":
                    qemu_args["-m"] = "%uM"%((int(value[0])*1024*0.70)/1024/1024);
                    return;

def setup_fs(paths=()):
    """Prepare the root filesystem for KVM under /mnt/self - this is simply our /
    without all the virtual filesystems docker creates"""
    # Mount / into /mnt/self to get rid of all virtual filesystems
    mnt = "/mnt/self"
    create_mount(mnt);
    subprocess.check_call(["mount","--bind","/",mnt]);

    # Getting rid of the docker mounts in /etc/ is obnoxious because the mount
    # point file is EBUSY as long as a mount is using it, even if we no longer
    # see the mount. Use overlayfs on /mnt/self/etc/
    upper = "/mnt/upper";
    work = "/mnt/work";
    for I in (upper,work):
        if os.path.isdir(I):
            shutil.rmtree(I);
        os.mkdir(I);

    with open(os.path.join(upper,"hostname"),"w") as out:
        with open("/etc/hostname") as F:
            out.write(F.read());

    # Use resolved
    # In Xenial resolved returns failures immediately after network-online.target
    #with open(os.path.join(upper,"resolv.conf"),"w") as F:
    #    print >> F,"namesever 127.0.0.53";
    # Still use resolved, but talk directly to the dns server, not the proxy
    os.symlink("/run/systemd/resolve/resolv.conf",os.path.join(upper,"resolv.conf"));

    subprocess.check_call(["mount","-t","overlay",
                           "-o","lowerdir=/etc,upperdir=%s,workdir=%s"%(upper,work),
                           "none",
                           os.path.join(mnt,"etc")]);

    # Mount other filesystems from fstab. This lets us have our kernel tree on NFS
    prefixes = get_fs_tab();
    to_mount = set();
    for I in paths:
        for J in prefixes:
            if I.startswith(J):
                to_mount.add(J);
    for I in sorted(to_mount,
                    key=lambda x:(len(x),x),reverse=True):
        create_mount(I);
        subprocess.check_call(["mount",I]);
        subprocess.check_call(["mount","--bind",I,os.path.join(mnt,I[1:])]);

    # Setup plan9 virtfs
    qemu_args["-fsdev"] = "local,id=host_fs,security_model=passthrough,path=%s"%(mnt);
    qemu_args["-device"].add("virtio-9p-pci,fsdev=host_fs,mount_tag=/dev/root");

def set_kernel(tree):
    """Use a compiled kernel tree as the boot kernel. This directly boots the
    bzimage in that tree and configures the KVM root filesystem to have a
    /lib/modules directory with symlinks back to the source tree. /boot/ is
    also setup in the usual way with symlinks."""
    bzimage = os.path.join(tree,"arch/x86/boot/bzImage");
    ver = get_ip_tag(subprocess.check_output(["file",bzimage]),"version");

    mdir = "/lib/modules/%s"%(ver);
    if os.path.isdir(mdir):
        shutil.rmtree(mdir);
    os.makedirs(mdir);

    files = subprocess.check_output(["find",tree,
                                     "-name","modules.builtin",
                                     "-or",
                                     "-name","modules.order",
                                     "-or",
                                     "-name","*.ko"]).split()

    # Do not want to run 'make modules_install' so make these by hand..
    with open(os.path.join(mdir,"modules.builtin"),"w") as out:
        for I in files:
            if I.endswith("modules.builtin"):
                with open(I) as F:
                    out.write(F.read());

    with open(os.path.join(mdir,"modules.order"),"w") as out:
        for I in files:
            if I.endswith("modules.builtin"):
                with open(I) as F:
                    out.write(F.read());

    # Symlink modules
    mdir = os.path.join(mdir,"modules");
    if not os.path.isdir(mdir):
        os.makedirs(mdir);
    for I in files:
        if I.endswith(".ko"):
            os.symlink(I,os.path.join(mdir,os.path.basename(I)));

    if os.path.isdir("/boot"):
        shutil.rmtree("/boot");
    os.makedirs("/boot");

    os.symlink(os.path.join(tree,"System.map"),"/boot/System.map-%s"%(ver));
    os.symlink(os.path.join(tree,".config"),"/boot/config-%s"%(ver));
    os.symlink(bzimage,"/boot/vmlinuz-%s"%(ver));

    subprocess.check_call(["depmod","-a",ver]);

    qemu_args.update({
        "-kernel": os.path.join(tree,"arch/x86/boot/bzImage"),
        # to debug:  systemd.journald.forward_to_console=1 systemd.log_level=debug
        # Change and enable debug-shell.service to use /dev/console
        "-append": 'root=/dev/root rw rootfstype=9p rootflags=trans=virtio console=ttyS0'
    });

def fixup_ipv6(mac,tap):
    """qemu does not connect the rxfilter of the guest to the macvtap, we can do
    this via QMP with the query-rx-filter stuff and related event, but for our
    uses we just need IPv6 SNM to work without secondary IPs, so this is
    enough for now."""
    mac = mac.split(':');
    addrs = set();
    addrs.add(":".join(("33","33","ff",mac[3],mac[4],mac[5]))); # ff02::1:ff<mac>
    addrs.add("33:33:00:01:00:03"); # ff02::1:3
    addrs.add("01:00:5e:00:00:fc"); # 224.0.0.252
    for I in addrs:
        subprocess.check_call(["ip","netns","exec","kvm",
                               "ip","maddress","add",I,"dev",tap]);

def mac_to_host(mac):
    mac = [int(I,16) for I in mac.split(":")];
    ipv6 = "fe80::%02x%02x:%02xff:fe%02x:%02x%02x"%(
        mac[0] ^ 0x2,mac[1],
        mac[2],mac[3],
        mac[4],mac[5]);
    # Cannonize the IPv6 numeric
    return socket.inet_ntop(socket.AF_INET6,socket.inet_pton(socket.AF_INET6,ipv6));

def setup_net():
    """Create a netnamespace and put a macvlan into it, then wire that up as the
    tap device to use with qemu. This is the easiest way to get kvm setup
    without having to mess with bridges/etc"""

    # The master interface is the one with the public facing route.
    master = get_ip_tag(subprocess.check_output(["ip","route","get","8.8.8.8"]),
                        "dev");
    master_mac = get_ip_tag(subprocess.check_output(["ip","link","show","dev",master]),
                            "link/ether");
    tap_if_mac = list(master_mac.split(":"));

    # Set locally administered bit
    tap_if_mac[0] = "%02x"%(int(tap_if_mac[0],16) | 0x2);

    for I in subprocess.check_output(["ip","netns","list"]).split():
        if I == "kvm":
            subprocess.check_call(["ip","netns","del",I]);

    # The netns is a mount in our container's mount ns so when the container
    # gets deleted so does the ns and the macvlan interface we create
    subprocess.check_call(["ip","netns","add","kvm"]);

    # It is really weird that macvtap interfaces can have an IP.. Disable IPv6
    # and thus DAD/radv/etc. Moving it into a ns ensures that networkd doesn't
    # try and do dhcp either.
    subprocess.check_call(["ip","netns","exec","kvm",
                           "bash","-c","echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6"]);

    tap = "macvtap0";
    subprocess.check_call(["ip","link","add",
                           "link",master,
                           # Setting the index makes sure we only create one of these at once, due to how we create the MAC.
                           "index","123",
                           "name",tap,
                           "type","macvtap",
                           "mode","bridge",
    ]);
    subprocess.check_call(["ip","link","set",tap,"netns","kvm"]);
    subprocess.check_call(["ip","netns","exec","kvm",
                           "ip","link","set","dev",tap,
                           "address",":".join(tap_if_mac)]);

    tap_if = subprocess.check_output(["ip","netns","exec","kvm",
                                     "ip","link","show","dev",tap]);
    tap_if_idx = int(tap_if.partition(':')[0]);
    tap_if_mac = get_ip_tag(tap_if,"link/ether");

    fixup_ipv6(tap_if_mac,tap);

    subprocess.check_call(["ip","netns","exec","kvm",
                           "ip","link","set","up","dev","lo"]);
    subprocess.check_call(["ip","netns","exec","kvm",
                           "ip","link","set","up","dev",tap]);

    global net_tap;
    net_tap = open("/rdev/tap%u"%(tap_if_idx),"r+");

    # fixme new style
    qemu_args["-netdev"] = "tap,id=network0,fd=%u"%(net_tap.fileno());
    qemu_args["-device"].add("virtio-net-pci,netdev=network0,mac=%s"%(tap_if_mac));

    # Make port 21 on our host proxy to ssh on the kvm
    # macvlan prevents hair pin to the master interface entirely.. Maybe fork into the netns and use a 2nd macvlan interface?
    #subprocess.Popen(["socat","TCP6-LISTEN:21,reuseaddr,fork",
    #                  "TCP6:[%s%%%s]:22"%(mac_to_host(tap_if_mac),master)]);

def match_modalias(modalias):
    """Detect pass through PCI devices"""
    # Fom /lib/modules/4.4.0-53-generic/modules.alias
    matches = [
        "pci:v000015B3d00001010sv*sd*bc*sc*i*",
        "pci:v000015B3d0000100Fsv*sd*bc*sc*i*",
        "pci:v000015B3d0000100Esv*sd*bc*sc*i*",
        "pci:v000015B3d0000100Dsv*sd*bc*sc*i*",
        "pci:v000015B3d0000100Csv*sd*bc*sc*i*",
        "pci:v000015B3d0000100Bsv*sd*bc*sc*i*",
        "pci:v000015B3d0000100Asv*sd*bc*sc*i*",
        "pci:v000015B3d00001009sv*sd*bc*sc*i*",
        "pci:v000015B3d00001008sv*sd*bc*sc*i*",
        "pci:v000015B3d00001007sv*sd*bc*sc*i*",
        "pci:v000015B3d00001006sv*sd*bc*sc*i*",
        "pci:v000015B3d00001005sv*sd*bc*sc*i*",
        "pci:v000015B3d00001004sv*sd*bc*sc*i*",
        "pci:v000015B3d00001003sv*sd*bc*sc*i*",
        "pci:v000015B3d00001002sv*sd*bc*sc*i*",
        "pci:v000015B3d0000676Esv*sd*bc*sc*i*",
        "pci:v000015B3d00006746sv*sd*bc*sc*i*",
        "pci:v000015B3d00006764sv*sd*bc*sc*i*",
        "pci:v000015B3d0000675Asv*sd*bc*sc*i*",
        "pci:v000015B3d00006372sv*sd*bc*sc*i*",
        "pci:v000015B3d00006750sv*sd*bc*sc*i*",
        "pci:v000015B3d00006368sv*sd*bc*sc*i*",
        "pci:v000015B3d0000673Csv*sd*bc*sc*i*",
        "pci:v000015B3d00006732sv*sd*bc*sc*i*",
        "pci:v000015B3d00006354sv*sd*bc*sc*i*",
        "pci:v000015B3d0000634Asv*sd*bc*sc*i*",
        "pci:v000015B3d00006340sv*sd*bc*sc*i*",
        "pci:v000015B3d00001016sv*sd*bc*sc*i*",
        "pci:v000015B3d00001015sv*sd*bc*sc*i*",
        "pci:v000015B3d00001014sv*sd*bc*sc*i*",
        "pci:v000015B3d00001013sv*sd*bc*sc*i*",
        "pci:v000015B3d00001012sv*sd*bc*sc*i*",
        "pci:v000015B3d00001011sv*sd*bc*sc*i*",
    ];
    for I in matches:
        if fnmatch.fnmatch(modalias,I):
            return True;
    return False;

def switch_to_vfio(bdf,modalias):
    """Switch the kernel driver for a PCI device to vfio-pci so it can be used
    with VFIO passthrough."""
    cur_driver = os.path.join("/sys/bus/pci/devices",bdf,"driver");
    if os.path.exists(cur_driver):
        if os.readlink(cur_driver).endswith("vfio-pci"):
            return;

    # There kernel does not de-dup this list and provides no wy for us to
    # see, it so, remove then add.
    with open("/sys/bus/pci/drivers/vfio-pci/remove_id","w") as F:
        try:
            print >> F,"%s %s"%(modalias['v'],modalias['d']);
            F.flush();
        except IOError, why:
            # can get enodev if there is no ID in the list
            pass;
    with open("/sys/bus/pci/drivers/vfio-pci/new_id","w") as F:
        print >> F,"%s %s"%(modalias['v'],modalias['d']);

    if os.path.exists(cur_driver):
        with open(os.path.join(cur_driver,"unbind"),"w") as F:
            print >> F,bdf;
    with open("/sys/bus/pci/drivers/vfio-pci/bind","w") as F:
        print >> F,bdf;

    assert os.readlink(cur_driver).endswith("vfio-pci");

def has_iommu():
    if not os.path.isdir("/sys/kernel/iommu_groups"):
        return False;
    for I in os.listdir("/sys/kernel/iommu_groups"):
        return True;
    return False;

def pass_hca():
    """Find RDMA HCAs and configure them for PCI passthrough"""
    # No hardware support for IOMMU, can't do it.
    if not has_iommu():
        return;

    # Find RDMA cards
    sd = "/sys/bus/pci/devices/";
    devices = {};
    for I in os.listdir(sd):
        with open(os.path.join(sd,I,"modalias")) as F:
            modalias = F.read().strip();
            if match_modalias(modalias):
                modalias = {a: b for a,b in re.findall(r"([a-z]+)([0-9A-F]+)",modalias)};
                devices[I] = modalias;

    if not devices:
        return;

    # Docker mounts sysfs ro, we need a writable mount to mess with the driver
    # attachment
    subprocess.check_call(["mount","-o","remount,rw","/sys"]);

    for bdf,modalias in devices.iteritems():
        switch_to_vfio(bdf,modalias);
        # This seems totally undocumented.
        qemu_args["-device"].add("vfio-pci,host=%s"%(bdf));

parser = argparse.ArgumentParser(description='Launch kvm using the filesystem from the container');
parser.add_argument('--kernel',required=True);
args = parser.parse_args()

qemu_args = {
    "-enable-kvm": None,
    # Escape sequence is ctrl-a c q
    "-nographic": None,
    "-machine": "q35",
    "-cpu": "host",
    "-vga": "none",
    "-no-reboot": None,
    "-device": {"virtio-serial-pci","virtio-rng-pci","virtio-balloon-pci"},
};

pass_hca()

setup_mem();
setup_fs(paths=[args.kernel]);
set_kernel(args.kernel);
setup_net();

cmd = ["ip","netns","exec","kvm","qemu-system-x86_64"];
for k,v in sorted(qemu_args.iteritems()):
    if isinstance(v,set) or isinstance(v,list):
        for I in v:
            cmd.append(k);
            cmd.append(I);
    else:
        cmd.append(k);
        if v:
            cmd.append(v);
print cmd
os.execvp(cmd[0],cmd);
