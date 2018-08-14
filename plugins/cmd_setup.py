"""Setup all needed pieces on hypervisor
"""
import os
import utils
from utils.config import init, load, username, group
import platform
import subprocess
import shutil
from utils.cmdline import *

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
    # TODO: rewrite it with Ansible to support other HV
    # Expectations that developers will get this tool from PATH in their bashrc
    # and it will be located in shared folder, however the tool itself can work
    # from any place, including offline.
    # 1. Check that we are running Fedora
    # 1.2 Running on HV
    # 1.3 Has proper IOMMU kernel config
    # 2. Ask and check provided directories
    # 3. Update to latest packages
    # 4. Install docker
    # 5. Setup docker
    # 6. Send an email with howtos and help

    if not args.dirs:
        args.kernel = False
        args.rdma_core = False
        args.iproute = False

    if args.installs:
        print(""" This setup script will update your hypervisor to latest
 distribution packages and install docker. Please restart
 the hypervisor to complete the installation. """)
        if args.yes is False and query_yes_no("Do you want to proceed?",
                                              'no') is False:
            exit("Exiting ...")

    supported_os = {
        'fedora',
        'ubuntu',
    }

    dist = platform.dist()
    distro = dist[0].lower()
    if distro not in supported_os:
        exit("""  Your hypervisor is not supported.
  This script works on Fedora only. Exiting ...""")

    if args.installs:
        setuphv = utils.get_internal_fn('scripts/')
        setuphv += 'setup-hv.' + distro
        subprocess.check_call(setuphv)

    init()
    section = load()

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
            subprocess.call(["sudo", "chown", "-R", username + ":" + group, value])

            if key == "src" or key == "logs" or key == "ccache":
                continue

            p = subprocess.Popen(
                [
                    "git", "clone", "ssh://" + username +
                    "@l-gerrit.mtl.labs.mlnx:29418/upstream/" + key, "."
                ],
                cwd=value)
            p.wait()

            p = subprocess.Popen(
                [
                    "scp", "-p", "-P", "29418",
                    username + "@l-gerrit.mtl.labs.mlnx:hooks/commit-msg",
                    ".git/hooks/"
                ],
                cwd=value)
            p.wait()

            if key == "kernel":
                shutil.copy(
                    section['linux'] + "/.config",
                    os.path.join(
                        os.path.dirname(__file__), "../configs/kconfig-kvm-ib"))
                p = subprocess.Popen(["make", "olddefconfig"], cwd=value)
                p.wait()

    print("Completed, PLEASE RESTART server")
