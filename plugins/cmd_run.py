"""Run container with proper FS and kernel
"""
import os
import sys
import stat
import pwd
import grp
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
            res.append("%s:%s:Z" % (I, I))
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

def get_virt_rdma_devices():
    # In the future, it will support siw too and we will generate
    # automatically the list of interfaces, and fix initialization
    # over loopback.
    return [ 'rxe-eth0' ]

def get_simx_rdma_devices():
    return [
        'cx4-ib', 'cx4-eth', 'cx5-ib', 'cx5-eth',
        'cx5ex-eth', 'cib-ib', 'cx4lx-eth',
        'cx6-ib', 'cx6-eth', 'cx6dx-eth', 'cx6lx-eth',
        'cx7-ib', 'cx7-eth'
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

def get_host_name(cname):
    """Return the host name of the docker container"""
    return cname[8:]

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

    for host, inf in sorted(hosts.items(), reverse=True):
        if host == hostname or host == hostname + '-ilo':
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
    gr = grp.getgrgid(os.getgid())
    p = {
        "user": usr.pw_name,
        "group": gr.gr_name,
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
    if args.virt:
        p["virt"] = sorted(args.virt)
#    p["mem"] = str(mem) + '8G'
    p["mem"] = '8G'

    if args.boot_script:
        p["boot_script"] = args.boot_script

    if args.image:
        try:
            p["num_of_vfs"] = utils.get_images(args.image)['num_of_vfs']
        except KeyError:
            pass
        try:
            p["num_ports"] = utils.get_images(args.image)['num_ports']
        except KeyError:
            pass

    if args.custom_qemu:
        p["custom_qemu"] = args.custom_qemu

    if args.gdbserver:
        p["gdbserver"] = args.gdbserver

    return base64.b64encode(pickle.dumps(p)).decode()

def validate_and_set_boot(args):
    if not args.image:
        return None

    if not args.boot_script:
        try:
            args.boot_script = utils.get_images(args.image)['boot_script']
        except KeyError:
            pass

    if not args.boot_script:
        return None

    try:
        executable = stat.S_IXUSR & os.stat(args.boot_script)[stat.ST_MODE]
    except FileNotFoundError:
        exit("Wrong path to boot script. Exiting ...")

    if not executable:
        exit("Bootup script needs to be executable. Exiting ...")

    with open(args.boot_script, 'r') as f:
        if not f.readline().startswith("#!"):
            exit("Missing shebang in the first line of boot script. Exiting ...")

    return args.boot_script

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
        help="Path to the top of a compiled kernel source tree to boot",
        default=None)
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
    parser.add_argument(
        '--virt',
        metavar="VIRT_DEV",
        action="append",
        default=[],
        choices=sorted(get_virt_rdma_devices()),
        help="Pass a virtual device type-interface format to the guest")
    parser.add_argument(
        '--boot-script',
        help="Path to the custom boot script which will be executed after boot",
        default=None)
    parser.add_argument(
        '--gdbserver',
        metavar='PORT',
        type=int,
        help="TCP port for QEMU's GDB server",
        default=None)

def cmd_run(args):
    """Run a system image container inside KVM"""
    from . import cmd_images
    section = utils.load_config_file()
    docker_os = section.get('os', cmd_images.default_os)

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
        try:
            args.kernel = utils.get_images(args.image)['kernel']
        except KeyError:
            pass

    if args.kernel is None:
        args.kernel = section.get('kernel', None)

    union = set(get_simx_rdma_devices()).union(
        set(get_pci_rdma_devices().keys())).union(
        set(get_virt_rdma_devices()))

    if not set(s).issubset(union):
        # It is possible only for config files, because we sanitized
        # input to ensure that valid data is supplied.
        exit(
            "There is an error in configuration file, PCI, SIMX or VIRT devices don't exists."
        )

    args.pci += set(s).intersection(set(get_pci_rdma_devices().keys()))
    args.virt += set(s).intersection(set(get_virt_rdma_devices()))
    b = args.pci + args.virt
    args.simx += [item for item in s if item not in b]

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
        print (args.kernel)
        args.kernel = os.path.realpath(args.kernel)
        if not os.path.isdir(args.kernel):
            raise ValueError("Kernel path %r is not a directory/does not exist"
                             % (args.kernel))
        mapdirs.add(args.kernel)
        print (mapdirs)

    if args.image:
        try:
            if utils.get_images(args.image)['custom_qemu'] != "true":
                raise KeyError
            args.custom_qemu = section.get('simx', None)
        except KeyError:
            args.custom_qemu = None
    else:
        args.custom_qemu = None

    if args.custom_qemu:
        args.custom_qemu = os.path.realpath(args.custom_qemu)
        if not os.path.isdir(args.custom_qemu):
            raise ValueError("SimX path %r is not a directory/does not exist"
                             % (args.custom_qemu))
        mapdirs.add(args.custom_qemu)

    usr = pwd.getpwuid(os.getuid())
    args.dir.append(usr.pw_dir)
    if 'dir' in section:
        args.dir += section['dir'].split()
    args.dir = list(set(args.dir))

    for I in args.dir:
        mapdirs.add(I)

    args.boot_script = validate_and_set_boot(args)
    if args.boot_script:
        mapdirs.add(os.path.dirname(args.boot_script))

    vm_addr = get_mac()

    if args.run_shell:
        do_kvm_args = ["/bin/bash"]
    else:
        do_kvm_args = ["python3", "/plugins/do-kvm.py"]
#        do_kvm_args = ["python3", "/plugins/do-test.py"]
        if vm_addr.ip:
            # Open network for QEMU, relevant for bridged mode only
            iprule = ["FORWARD", "-m", "physdev", "--physdev-is-bridged", "-j", "ACCEPT"]
            # First delete old rule
            subprocess.call(["sudo", "iptables", "-D"] + iprule,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
            subprocess.call(["sudo", "iptables", "-I"] + iprule,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)

    src_dir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))

    ssh = False
    if args.pci:
        # chack if we have container running with bound PCI device to it
        # sudo docker ps --filter "label=pci" --format "{{.Names}}"
        # sudo docker inspect --format='{{.Config.Labels.pci}}' mkt_run_nps-server-14-015
        cont = docker_get_containers(label="pci")
        for c in cont:
            c = c.decode()[1:-1]
            cpci = docker_output(["inspect", "--format", '"{{.Config.Labels.pci}}"', c])
            cpci = cpci.decode()[2:-2].split(', ')
            cpci = [x[1:-1] for x in cpci]
            common = set(cpci).intersection(set(args.pci))
            if common:
                ssh = True;
                cname = c;

    if ssh:
        subprocess.call(["ssh", "root@%s" % (get_host_name(cname))])
    else:
        cname = get_container_name(vm_addr)
        print (mapdirs.as_docker_bind())
        docker_exec(["run"] + mapdirs.as_docker_bind() + [
            "-v",
            "%s:/plugins:ro,Z" % (src_dir),
            "--mount",
            "type=bind,source=%s,destination=/logs" % (utils.config.runtime_logs_dir),
            "--rm",
            "--net=host",
            "--privileged",
            "--name=%s" % (cname),
            "--tty",
            "-l",
            "pci=%s" % (args.pci),
            "--hostname",
            vm_addr.hostname,
            "-e",
            "KVM_PICKLE=%s" % (get_pickle(args, vm_addr)),
            "--interactive",
            make_image_name("kvm", docker_os),
        ] + do_kvm_args)
