"""Setup all needed pieces on hypervisor
"""
import os
import utils
import subprocess
import shutil
import tempfile

def args_setup(parser):
    parser.add_argument(
        "-y",
        "--assume-yes",
        dest="yes",
        action="store_true",
        help="Automatically answer yes for all questions",
        default=False)
    parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        help="Remove existing directories",
        default=False)
    parser.add_argument(
        "--no-dirs",
        dest="dirs",
        action="store_false",
        help="Do not clone and create ANY directory (kernel, rdma-core and iproute2)",
        default=True)
    parser.add_argument(
        "--no-kernel",
        dest="kernel",
        action="store_false",
        help="Do not clone and create kernel directory",
        default=True)
    parser.add_argument(
        "--no-rdma-core",
        dest="rdma_core",
        action="store_false",
        help="Do not clone and create rdma-core directory",
        default=True)
    parser.add_argument(
        "--no-iproute2",
        dest="iproute",
        action="store_false",
        help="Do not clone and create iproute2 directory",
        default=True)
    parser.add_argument(
        "--no-installs",
        dest="installs",
        action="store_false",
        help="""Skip hypervisor packages installation and configuration.
           It can be useful if you was asked to work on already pre-configured
           system""",
        default=True)

def cmd_setup(args):
    """Setup environment."""

    if not args.dirs:
        args.kernel = False
        args.rdma_core = False
        args.iproute = False

    if args.installs:
        print(""" This setup script will update your hypervisor to latest
 distribution packages and install docker. Please restart
 the hypervisor to complete the installation. """)
        if args.yes is False and utils.query_yes_no("Do you want to proceed?", 'no') is False:
            exit("Exiting ...")

    supported_os = {
            'fedora' : '26',
            'ubuntu' : '16',
            'rhel' : '8',
            'redhat' : '8',
            'centos' : '8',
    }

    # Python API stability is dissaster
    # module platform was deprecated https://docs.python.org/3/library/platform.html
    # Luckily enough, they added distro module before removing platform
    try:
        import distro
        distro_id = distro.id()
        distro_v = distro.major_version()
    except ModuleNotFoundError:
        import platform
        distro_id = platform.dist()[0].lower()
        distro_v = platform.dist()[1].split('.')[0]

    if distro_id not in supported_os.keys() or distro_v < supported_os[distro_id]:
        exit("""  Your hypervisor is not supported. Exiting ...""")

    if args.installs:
        setuphv = utils.get_internal_fn('scripts/')
        if distro_id == 'redhat':
            distro_id = 'rhel'
        setuphv += 'setup-hv.' + distro_id
        subprocess.check_call(setuphv)

    utils.init_config_file()
    section = utils.load_config_file()

    if args.dirs:
        for key, value in section.items():
            if args.force:
                subprocess.call(["sudo", "rm", "-rf", value])
            if os.path.exists(value):
                exit("Please remove " + value + " Exiting ...")

            if key == "kernel" and not args.kernel:
                continue
            if key == "rdma-core" and not args.rdma_core:
                continue
            if key == "iproute2" and not args.iproute:
                continue

            if key == 'os':
                continue

            print("Prepare " + key)
            subprocess.call(["sudo", "mkdir", "-p", value])
            subprocess.call(["sudo", "chown", "-R", utils.username() + ":" + utils.group(), value])

            if key == "src" or key == "logs" or key == "ccache":
                continue

            if key == "kernel":
                key = "linux"

            p = subprocess.Popen(
                [
                    "git", "clone", "ssh://" + utils.username() +
                    "@l-gerrit.mtl.labs.mlnx:29418/upstream/" + key, "."
                ],
                cwd=value)
            p.wait()

            p = subprocess.Popen(
                [
                    "scp", "-p", "-P", "29418",
                    utils.username() + "@l-gerrit.mtl.labs.mlnx:hooks/commit-msg",
                    ".git/hooks/"
                ],
                cwd=value)
            p.wait()

            if key == "linux":
                shutil.copy(
                    os.path.join(
                        os.path.dirname(__file__), "../configs/kconfig-kvm"),
                    value + "/.config")

    print("Completed, PLEASE RESTART server")

#--------------------------------------------------------------------------------------------------------
def args_setup_master(parser):
     parser.add_argument(
        "hostnames",
        nargs='+',
        help="List of slaves to connect")
     parser.add_argument(
        "-y",
        "--assume-yes",
        dest="yes",
        action="store_true",
        help="Automatically answer yes for all questions",
        default=False)
     parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        help="Remove existing directories",
        default=False)
     parser.add_argument(
        "--export-only",
        dest="export",
        action="store_true",
        help="Skip installation stage and update NFS shares only",
        default=False)

def cmd_setup_master(args):
    ''' Setup proper master environment and export it to slaves '''
    if not args.export:
        cmd = ["mkt", "setup"]
        if args.yes:
            cmd.append("-y")
        if args.force:
            cmd.append("-f")

        subprocess.call(cmd)

    utils.init_config_file()
    section = utils.load_config_file()

    with tempfile.NamedTemporaryFile("w") as f:
        f.write(open("/etc/exports").read())
        for host in args.hostnames:
            export = section['src'] + "\t" + \
                     str(host) + "(ro,async,no_subtree_check,no_root_squash)" + \
                     "\n" + section['logs'] + "\t" + \
                     str(host) + "(rw,async,no_subtree_check,no_root_squash)" + "\n"
            f.write(export)
            f.flush()
        subprocess.call(["sudo", "cp", f.name, "/etc/exports"])

    subprocess.call(["sudo", "exportfs", "-r"])

#--------------------------------------------------------------------------------------------------------
def args_setup_slave(parser):
     parser.add_argument(
        "hostname",
        nargs=1,
        help="Master server to connect this slave")
     parser.add_argument(
        "-y",
        "--assume-yes",
        dest="yes",
        action="store_true",
        help="Automatically answer yes for all questions",
        default=False)
     parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        help="Remove existing directories",
        default=False)
     parser.add_argument(
        "--export-only",
        dest="export",
        action="store_true",
        help="Skip installation stage and update NFS shares only",
        default=False)

def cmd_setup_slave(args):
    ''' Setup proper slave environment and connect to master server '''
    if not args.export:
        cmd = ["mkt", "setup", "--no-dirs"]
        if args.yes:
            cmd.append("-y")
        if args.force:
            cmd.append("-f")

        subprocess.call(cmd)

    utils.init_config_file()
    section = utils.load_config_file()

    subprocess.call(["sudo", "mkdir", "-p", section['src']])
    subprocess.call(["sudo", "chown", "-R", utils.username() + ":" + utils.group(), section['src']])
    subprocess.call(["sudo", "mkdir", "-p", section['logs']])
    subprocess.call(["sudo", "chown", "-R", utils.username() + ":" + utils.group(), section['logs']])

    with tempfile.NamedTemporaryFile("w") as f:
        f.write(open("/etc/fstab").read())
        export = args.hostname[0] + ":" + \
                section['src'][:-1] + "\t" + section['src'][:-1] + \
                 "\t" + "nfs" + "\t" + "ro,nolock 0 0" + "\n" + \
                 args.hostname[0] + ":" + \
                 section['logs'][:-1] + "\t" + section['logs'][:-1] + \
                 "\t" + "nfs" + "\t" + "rw,nolock 0 0" + "\n"
        f.write(export)
        f.flush()
        subprocess.call(["sudo", "cp", f.name, "/etc/fstab"])

    subprocess.call(["sudo", "mount", "-a", "-t", "nfs", "-o", "remount"])
#--------------------------------------------------------------------------------------------------------
def args_reconnect_slave(parser):
    pass

def cmd_reconnect_slave(args):
    ''' Reconnect slave in case master was rebooted '''
    subprocess.call(["sudo", "mount", "-a", "-t", "nfs", "-o", "remount"])
