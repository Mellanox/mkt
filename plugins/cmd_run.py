"""Run container with proper FS and kernel
"""
import os
import sys
import pwd
import pickle
import base64
import fnmatch
import re
import inspect
import utils
import socket
import collections
import random
from utils.docker import *
from utils.cmdline import *
from . import cmd_images

VM_Addr = collections.namedtuple("VM_Addr", "hostname ip mac")


class DirList(object):
    def __init__(self):
        self.list = set()

    def add(self, dfn):
        """Maintain a list of directories such that there are no subdirectories of
        other elements in the list."""
        if isinstance(dfn, bytes):
            dfn = dfn.decode()
        while dfn[-1] == '/':
            dfn = dfn[:-1]

        dfn = os.path.realpath(dfn)

        torm = set()
        for I in self.list:
            if dfn.startswith(I):
                return
            if I.startswith(dfn):
                torm.add(I)
        self.list.difference_update(torm)
        self.list.add(dfn)

    def as_docker_bind(self):
        res = []
        for I in sorted(self.list):
            res.append("-v")
            res.append("%s:%s" % (I, I))
        return res


def match_modalias(modalias):
    """Detect Mellanox devices that we want to pass through"""
    # Fom /lib/modules/4.18.rc1/modules.alias
    matches = [
        "pci:v000015B3d0000A2D3sv*sd*bc*sc*i*",
        "pci:v000015B3d0000A2D2sv*sd*bc*sc*i*",
        "pci:v000015B3d0000101Csv*sd*bc*sc*i*",
        "pci:v000015B3d0000101Bsv*sd*bc*sc*i*",
        "pci:v000015B3d0000101Asv*sd*bc*sc*i*",
        "pci:v000015B3d00001019sv*sd*bc*sc*i*",
        "pci:v000015B3d00001018sv*sd*bc*sc*i*",
        "pci:v000015B3d00001017sv*sd*bc*sc*i*",
        "pci:v000015B3d00001018sv*sd*bc*sc*i*",
        "pci:v000015B3d00001017sv*sd*bc*sc*i*",
        "pci:v000015B3d00001016sv*sd*bc*sc*i*",
        "pci:v000015B3d00001015sv*sd*bc*sc*i*",
        "pci:v000015B3d00001014sv*sd*bc*sc*i*",
        "pci:v000015B3d00001013sv*sd*bc*sc*i*",
        "pci:v000015B3d00001012sv*sd*bc*sc*i*",
        "pci:v000015B3d00001011sv*sd*bc*sc*i*",
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
        "pci:v000015B3d00006340sv*sd*bc*sc*i*"
    ]
    for I in matches:
        if fnmatch.fnmatch(modalias, I):
            return True
    return False


def has_iommu():
    if not os.path.isdir("/sys/kernel/iommu_groups"):
        return False
    for I in os.listdir("/sys/kernel/iommu_groups"):
        return True
    return False


def get_simx_rdma_devices():
    return [
        'cx4-ib', 'cx4-eth', 'cx5-ib', 'cx5-eth',
        'cib-ib', 'cx4lx-eth', 'cx6-ib', 'cx6-eth'
    ]


def get_pci_rdma_devices():
    """Return a dictionary of PCI BDF to decoded mod aliases"""
    if not has_iommu():
        return {}

    sd = "/sys/bus/pci/devices/"
    devices = {}
    for I in os.listdir(sd):
        with open(os.path.join(sd, I, "modalias")) as F:
            modalias = F.read().strip()
            if match_modalias(modalias):
                modalias = {
                    a: b
                    for a, b in re.findall(r"([a-z]+)([0-9A-F]+)", modalias)
                }
                devices[I] = modalias
    return devices


def get_container_name(vm_addr):
    """Return the name of the docker container to use for this VM"""
    return "mkt_run_%s" % (vm_addr.hostname)


def random_mac():
    random.seed()
    a = random.randint(0, 255)
    b = random.randint(0, 255)
    c = random.randint(0, 255)
    d = random.randint(0, 255)
    mac = "52:54:%02x:%02x:%02x:%02x" % (a, b, c, d)
    return VM_Addr(mac=mac, ip=None, hostname=socket.gethostname() + "-vm")


def get_mac():
    list_fn = "/.autodirect/LIT/SCRIPTS/DHCPD/list.html"
    if not os.path.isfile(list_fn):
        return random_mac()

    # The file is very big and python is very slow, use grep to find the
    # relevant entries.
    hostname = socket.gethostname()
    o = subprocess.check_output(["grep", hostname, list_fn])
    hosts = {}
    for ln in o.splitlines():
        g = re.match(r"(.+?);\s+([0-f:]+?);\s+(.+?);\s+((?:.+?;\s+)+)<br>",
                     ln.decode())
        if g is None:
            continue
        hosts[g.group(3)] = (g.group(1), g.group(2))
    if not hosts:
        raise ValueError("The DHCP file %r could not be parsed for host %r" %
                         (list_fn, hostname))

    for host, inf in sorted(hosts.items()):
        if not host.startswith(hostname + "-0"):
            continue

        # docker is used to lock the MAC addresses, other virt systems should use
        # numbers at the end of the sorted range to try to avoid conflicting here.
        vm_addr = VM_Addr(ip=inf[0], mac=inf[1], hostname=host)
        cname = get_container_name(vm_addr)
        status = docker_output([
            "ps", "-a", "-q", "--filter",
            "name=%s" % (cname), "--format", "{{.Status}}"
        ])
        if status.startswith(b"Up"):
            continue
        return vm_addr

    # We only use MAC addresses from the table
    raise ValueError("The DHCP file %r could not be parsed for host %r" %
                     (list_fn, hostname))


def get_pickle(args, vm_addr):
    usr = pwd.getpwuid(os.getuid())

    p = {
        "user": usr.pw_name,
        "uid": usr.pw_uid,
        "gid": usr.pw_gid,
        "home": usr.pw_dir,
        "shell": usr.pw_shell,
        "vm_addr": vm_addr._asdict(),
    }

    if args.kernel_rpm is not None:
        p["kernel_rpm"] = args.kernel_rpm
    else:
        p["kernel"] = args.kernel

    # In GB: 2GB for real HW and 1 GB for SimX
    mem = 1
    if args.pci:
        p["vfio"] = sorted(args.pci)
        mem += 2 * len(p["vfio"])
    if args.simx:
        p["simx"] = sorted(args.simx)
        mem += len(p["simx"])
    p["mem"] = str(mem) + 'G'

    return base64.b64encode(pickle.dumps(p)).decode()


def args_run(parser):
    section = utils.load_config_file()
    parser.add_argument(
        "image",
        nargs='?',
        choices=sorted(utils.get_images()),
        help="The IB card configuration to use")

    kernel = parser.add_mutually_exclusive_group()
    kernel.add_argument(
        '--kernel',
        help="Path to the the top of a compiled kernel source tree to boot",
        default=section.get('linux', None))
    kernel.add_argument(
        '--kernel-rpm', help="Path to a kernel RPM to boot", default=None)

    parser.add_argument(
        '--dir', action="append", help="Other paths to map", default=[])
    parser.add_argument(
        '--simx',
        metavar='SIMX_DEV',
        action="append",
        default=[],
        choices=sorted(get_simx_rdma_devices()),
        help="Run using simx to create a mlx5 IB device")
    parser.add_argument(
        '--run-shell',
        action="store_true",
        default=False,
        help="Run a shell inside the container instead of invoking kvm")
    parser.add_argument(
        '--pci',
        metavar="PCI_BDF",
        action="append",
        default=[],
        choices=sorted(get_pci_rdma_devices().keys()),
        help="Pass a given PCI bus/device/function to the guest")


def cmd_run(args):
    """Run a system image container inside KVM"""
    section = utils.load_config_file()
    docker_os = section.get('os', 'fc28')

    # We have three possible options to execute:
    # 1. "mkt run" without request to specific image. We will try to find
    #    default one
    # 2. "mkt run --pci ..." or "mkt run --simx ...". We won't use default
    #    image but add supplied PCIs and SimX devices.
    # 3. "mkt run image_name --pci ..." or "mkt run image_name --simx ...". We
    #    will add those PCIs and SimX devices to the container.
    s = set()
    if not args.pci and not args.simx:
        if not args.image:
            args.image = section.get('image', None)

    if args.image:
        pci = utils.get_images(args.image)['pci']
        s = pci.split()

    union = set(get_simx_rdma_devices()).union(
        set(get_pci_rdma_devices().keys()))
    if not set(s).issubset(union):
        # It is possible only for config files, because we sanitized
        # input to ensure that valid data is supplied.
        exit(
            "There is an error in configuration file, PCI and/or SIMX devices don't exists."
        )

    args.pci += set(s).intersection(set(get_pci_rdma_devices().keys()))
    args.simx += set(s).intersection(set(get_simx_rdma_devices()))

    if len(args.simx) > 5:
        exit("SimX doesn't support more than 5 devices")

    if not args.kernel and not args.kernel_rpm:
        exit(
            "Must specify a linux kernel with --kernel, or a config file default"
        )

    # Invoke ourself as root to manipulate sysfs
    if args.pci:
        subprocess.check_call([
            "sudo", sys.executable,
            os.path.join(os.path.dirname(__file__), "../utils/vfio.py")
        ] + ["--pci=%s" % (I) for I in args.pci])

    mapdirs = DirList()
    if args.kernel_rpm is not None:
        args.kernel_rpm = os.path.realpath(args.kernel_rpm)
        if not os.path.isfile(args.kernel_rpm):
            raise ValueError(
                "Kernel RPM %r does not exist" % (args.kernel_rpm))
        mapdirs.add(os.path.dirname(args.kernel_rpm))
        args.kernel = None
    else:
        args.kernel = os.path.realpath(args.kernel)
        if not os.path.isdir(args.kernel):
            raise ValueError("Kernel path %r is not a directory/does not exist"
                             % (args.kernel))
        mapdirs.add(args.kernel)

    if not args.dir:
        usr = pwd.getpwuid(os.getuid())
        args.dir.append(usr.pw_dir)

    for I in args.dir:
        mapdirs.add(I)

    if args.run_shell:
        do_kvm_args = ["/bin/bash"]
    else:
        do_kvm_args = ["python3", "/plugins/do-kvm.py"]

    src_dir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))

    vm_addr = get_mac()
    cname = get_container_name(vm_addr)
    # Clean up a container if it is left over somehow
    cont = docker_get_containers(name=cname)
    if cont:
        try:
            docker_output(["kill", *cont])
        except subprocess.CalledProcessError:
            pass
        try:
            docker_output(["rm", *cont])
        except subprocess.CalledProcessError:
            pass

    docker_exec(["run"] + mapdirs.as_docker_bind() + [
        "-v",
        "%s:/plugins:ro" % (src_dir),
        "--rm",
        "--net=host",
        "--privileged",
        "--name=%s" % (cname),
        "--tty",
        "--hostname",
        vm_addr.hostname,
        "-e",
        "KVM_PICKLE=%s" % (get_pickle(args, vm_addr)),
        "--interactive",
        make_image_name("kvm", docker_os),
    ] + do_kvm_args)
