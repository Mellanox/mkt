"""Build docker images for different architectures and OS
"""
import os
import utils
from utils.git import *
from utils.docker import *
from subprocess import call, Popen

supported_os = {
    "fc28",
}

def args_images(parser):
    parser.add_argument(
        "--no-pull",
        dest="pull",
        action="store_false",
        help=
        "Do not update the base docker images from the public docker registry",
        default=True)
    parser.add_argument(
        "--push",
        action="store_true",
        help=
        "Upload created images to docker registry (need to have an account in harbor registry)",
        default=False)

    section = utils.load_config_file()
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


def do_pull(dockerfn):
    """This is like docker build --pull but it only pulls things that come
    from the public docker repositories, it does not indiscriminately pull
    other things"""
    images = set()
    with open(dockerfn, "rt") as F:
        for ln in F:
            if ln.startswith("FROM"):
                name = ln.split()[-1]
                if (name.startswith("fedora") or name.startswith("ubuntu")
                        or name.startswith("centos")):
                    images.add(name)
    return images


def cmd_images(args):
    """Build docker image for different architectures and OS."""

    with in_directory(utils.get_internal_fn(os.path.join("docker", args.os))):

        # Host network is needed because docker has a hard time in some cases
        # finding the right DNS server for Mellanox's private DNS. (eg over
        # VPN)
        cmd = ["build", "--network=host"] + get_proxy_arg()

        images = (
            (make_local_image_name("kvm_simx", args.os), "simx.Dockerfile"),
            (make_image_name("kvm", args.os), "kvm.Dockerfile"),
        )

        if args.pull:
            to_pull = set()
            for image, dockerfn in images:
                to_pull.update(do_pull(dockerfn))
            for I in to_pull:
                docker_call(["pull", I])

        for image, dockerfn in images:
            if args.pull:
                do_pull(dockerfn)

            docker_call(cmd + ["-t", image, "-f", dockerfn, "."])

    if args.push:
        docker_call(["login", docker_registry_name()])
        docker_call(["push", make_image_name("kvm", args.os)])
