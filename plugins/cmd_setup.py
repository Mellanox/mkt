"""Setup all needed pieces on hypervisor
"""
import os
from utils.config import init, load, username, group
import platform
import subprocess
import shutil
from utils.cmdline import *

def install_packages(distname):
    install_pkg = { 'fedora': (
                                "git",
                                "dnf-plugins-core",
                                "docker-ce",
                                "python3-argcomplete",
                                "pandoc",
                              )
                  }

    if distname == 'fedora':
        subprocess.call(['sudo', 'dnf',
                         '-y', 'install',
                         ' '.join(install_pkg['fedora'])])

def remove_packages(distname):
    remove_pkg = { 'fedora' : (
                                "docker",
                                "docker-client",
                                "docker-client-latest",
                                "docker-common",
                                "docker-latest",
                                "docker-latest-logrotate",
                                "docker-logrotate",
                                "docker-selinux",
                                "docker-engine-selinux",
                                "docker-engine"
                              )
                 }
    if distname == 'fedora':
        subprocess.call(['sudo', 'dnf',
                         '-y', 'remove',
                         ' '.join(remove_pkg['fedora'])],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

def configure_docker_repo(distname):
    if distname == 'fedora':
        subprocess.call([
            "sudo", "dnf", "config-manager", "--add-repo",
            "https://download.docker.com/linux/fedora/docker-ce.repo"
        ])

def services(distname):
    subprocess.call(["sudo", "systemctl", "enable", "docker"])
    subprocess.call(["sudo", "systemctl", "start", "docker"])

def upgrade_distro(distname):
    if distname == 'fedora':
        subprocess.call(["sudo", "dnf", "-y", "update"])

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
        help="Do not clone and create ANY directory (kernel, rdma-core and iproutes)",
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
        "--no-iproute",
        dest="iproute",
        action="store_false",
        help="Do not clone and create iproute2 directory",
        default=True)
    parser.add_argument(
        "--no-distupdate",
        dest="distupdate",
        action="store_false",
        help="Skip hypervisor distro packages update",
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

    check_not_root()

    if not args.dirs:
        args.kernel = False
        args.rdma_core = False
        args.iproute = False

    print(""" This setup script will update your hypervisor to latest
 distribution packages and install docker. Please restart
 the hypervisor to complete the installation. """)
    if args.yes is False and query_yes_no("Do you want to proceed?",
                                          'no') is False:
        exit("Exiting ...")

    supported_os = {
        "fedora",
    }

    dist = platform.dist()
    if dist[0] not in supported_os:
        exit("""  Your hypervisor is not supported.
  This script works on Fedora only. Exiting ...""")

    remove_packages(dist[0])
    configure_docker_repo(dist[0])
    install_packages(dist[0])
    services(dist[0])
    if args.distupdate:
        upgrade_distro(dist[0])

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

            print("Prepare " + key)
            subprocess.call(["sudo", "mkdir", "-p", value])
            subprocess.call(["sudo", "chown", "-R", username + ":" + group, value])

            if key == "src" or key == "logs" or key == "ccache":
                continue

            p = Popen(
                [
                    "git", "clone", "ssh://" + username +
                    "@l-gerrit.mtl.labs.mlnx:29418/upstream/" + key, "."
                ],
                cwd=value)
            p.wait()

            p = Popen(
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
                p = Popen(["make", "olddefconfig"], cwd=value)
                p.wait()

    print("Completed, PLEASE RESTART server")
