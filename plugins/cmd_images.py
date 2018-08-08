"""Build docker images for different architectures and OS
"""
import os
import utils.config
from utils.git import *
from utils.docker import *
from subprocess import call, Popen
from utils.cmdline import *

supported_os = {
    "fc28",
}

def args_images(parser):
    parser.add_argument(
        "--no-pull",
        dest="pull",
        action="store_false",
        help="Do not update the base image",
        default=True)

    section = utils.config.load()
    parser.add_argument(
        "os",
        nargs='?',
        help="The image to build",
        choices=sorted(supported_os),
        default=section.get('os', 'fc28'))
    """
    parser.add_argument("arch",
                        nargs='?',
                        help="Architecture to build",
                        choices=sorted([
                            "x86_64",
                            "arm64",
                            "ppc64",
                            "ppc64le",
                        ]),
                        default="x86_64");
    """


def get_proxy_arg(run=False):
    res = []
    if os.path.exists("/etc/apt/apt.conf.d/01proxy"):
        # The line in this file must be 'Acquire::http { Proxy "http://xxxx:3142"; };'
        with open("/etc/apt/apt.conf.d/01proxy") as F:
            proxy = F.read().strip().split('"')[1]
            if run:
                res.append("-e")
            else:
                res.append("--build-arg")
            res.append('http_proxy=%s' % (proxy))
    return res


def cmd_images(args):
    """Build docker image for different architectures and OS."""
    check_not_root()

    with in_directory(
            os.path.join(os.path.dirname(__file__), "../docker/", args.os)):
        # Host network is needed because docker has a hard time in some cases
        # finding the right DNS server for Mellanox's private DNS. (eg over
        # VPN)
        cmd = ["build", "--network=host"] + get_proxy_arg()

        # Pull can only be done for this image as the other FROMs in the later
        # images refer to internal images. Docker does not handle this well.
        docker_call(cmd + (["--pull"] if args.pull else ["--pull=false"]) + [
            "-t",
            make_local_image_name("kvm_base", args.os), "-f",
            "base.Dockerfile", "."
        ])

        docker_call(cmd + [
            "-t",
            make_local_image_name("kvm_simx", args.os), "-f",
            "simx.Dockerfile", "."
        ])

        docker_call(cmd + [
            "-t",
            make_image_name("kvm", args.os), "-f", "kvm.Dockerfile", "."
        ])
