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
from utils.docker import *
from utils.cmdline import *
from utils.config import *


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
        'cx4-ib', 'cx4-en', 'cx5-ib', 'cx5-en', 'cib', 'cx4lx', 'cx6-ib',
        'cx6-en'
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


# -------------------------------------------------------------------------


def switch_to_vfio(bdf, modalias):
    """Switch the kernel driver for a PCI device to vfio-pci so it can be used
    with VFIO passthrough."""
    cur_driver = os.path.join("/sys/bus/pci/devices", bdf, "driver")
    if os.path.exists(cur_driver):
        if os.readlink(cur_driver).endswith("vfio-pci"):
            return

    if not os.path.exists("/sys/bus/pci/drivers/vfio-pci"):
        subprocess.check_call(["modprobe", "vfio-pci"])

    # There kernel does not de-dup this list and provides no wy for us to
    # see, it so, remove then add.
    with open(
            "/sys/bus/pci/drivers/vfio-pci/remove_id", "wb", buffering=0) as F:
        val = "%s %s\n" % (modalias['v'], modalias['d'])
        try:
            F.write(val.encode())
            F.flush()
        except IOError:
            # can get enodev if there is no ID in the list
            pass
    with open("/sys/bus/pci/drivers/vfio-pci/new_id", "w") as F:
        F.write("%s %s\n" % (modalias['v'], modalias['d']))

    if os.path.exists(cur_driver):
        with open(os.path.join(cur_driver, "unbind"), "w") as F:
            F.write(bdf + "\n")
    with open("/sys/bus/pci/drivers/vfio-pci/bind", "w") as F:
        F.write(bdf + "\n")

    assert os.readlink(cur_driver).endswith("vfio-pci")


def args_vfio_enable(parser):
    parser.add_argument(
        '--pci',
        metavar="PCI_BDF",
        action="append",
        default=[],
        help="PCI BDF to move to vfio")


def cmd_vfio_enable(args):
    """Move the given PCI BDF to the vfio driver. This is an internal command used
    automatically by kvm-run"""
    sd = "/sys/bus/pci/devices/"
    for I in args.pci:
        with open(os.path.join(sd, I, "modalias")) as F:
            modalias = F.read().strip()
        modalias = {
            a: b
            for a, b in re.findall(r"([a-z]+)([0-9A-F]+)", modalias)
        }
        switch_to_vfio(I, modalias)


def get_mac():
    mac = None
    try:
        with open("/.autodirect/LIT/SCRIPTS/DHCPD/list.html") as F:
            mac = "00:50:56:1b:bc:10"
    except IOError:
        pass

    if not mac:
        import random
        random.seed()
        a = random.randint(0, 255)
        b = random.randint(0, 255)
        c = random.randint(0, 255)
        d = random.randint(0, 255)
        mac = "52:54:" + format(a, '02x') + ":" + format(
            b, '02x') + ":" + format(c, '02x') + ":" + format(d, '02x')

    return mac


def get_pickle(args):
    usr = pwd.getpwuid(os.getuid())
    mac = get_mac()

    p = {
        "user": usr.pw_name,
        "uid": usr.pw_uid,
        "gid": usr.pw_gid,
        "home": usr.pw_dir,
        "shell": usr.pw_shell,
        "kernel": args.kernel,
        "mac": mac,
    }
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

from . import cmd_images

def args_run(parser):
    section = load()
    parser.add_argument(
        "os",
        nargs=1,
        help="The OS image name to run",
        choices=sorted(cmd_images.supported_os),
        default=section.get('os', 'fc28'))
    parser.add_argument(
        "image",
        nargs='?',
        choices=sorted(get_images()),
        help="The IB card configuration to use")
    parser.add_argument('--kernel', help="Path to the kernel tree to boot",
                        default=section.get('linux',None))
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
    check_not_root()
    section = load()
    args.os = args.os[0];

    """
    We have three possible options to execute:
    1. "x run" without request to specific image. We will try to find default one
    2. "x run --pci ..." or "x run --simx ...". We won't use default image but add supplied
       PCIs and SimX devices.
    3. "x run image_nam --pci ..." or "x run image_nam --simx ...". We will add those PCIs
       and SimX devices to the container.
    """

    s = set()
    if not args.pci and not args.simx:
        if not args.image:
            args.image = section.get('image', None)

    if args.image:
        pci = get_imagesq(args.image)['pci']
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

    if not args.kernel:
        exit("Must specify a linux kernel with --kernel, or a config file default")

    # Invoke ourself as root to manipulate sysfs
    if args.pci:
        subprocess.check_call(["sudo", sys.argv[0], "vfio-enable"] +
                              ["--pci=%s" % (I) for I in args.pci])

    cont = docker_get_containers(name=args.os)
    if cont:
        try:
            docker_call(["kill", *cont])
        except subprocess.CalledProcessError:
            pass
        docker_call(["rm", *cont])

    args.kernel = os.path.realpath(args.kernel)
    if not os.path.isdir(args.kernel):
        raise ValueError(
            "Kernel path is not a directory/does not exist" % (args.kernel))

    mapdirs = DirList()
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

    docker_exec(["run"] + mapdirs.as_docker_bind() + [
        "-v",
        "%s:/plugins:ro" % (src_dir), "--rm", "--net=host", "--privileged",
        "--name=%s" % (args.os), "--tty", "-e",
        "KVM_PICKLE=%s" % (get_pickle(args)), "--interactive",
        make_image_name("kvm", args.os)
    ] + do_kvm_args)
