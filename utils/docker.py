import subprocess
import os
from utils.git import in_directory


def make_image_name(thing, version):
    return "harbor.mellanox.com/mkt/%s:%s" % (thing, version)


def make_local_image_name(thing, version):
    return "local_mkt/%s:%s" % (thing, version)


def docker_call(args):
    """Run docker and display the output to the terminal"""
    return subprocess.check_call([
        'sudo',
        'docker',
    ] + args)


def docker_exec(args):
    """Run docker and display the output to the terminal"""
    return os.execvp("sudo", [
        'sudo',
        'docker',
    ] + args)


def docker_output(args, mode=None):
    """Run docker and return the output"""
    o = subprocess.check_output([
        'sudo',
        'docker',
    ] + args)
    if mode == "raw":
        return o
    elif mode == "lines":
        return o.splitlines()
    elif mode is None:
        return o.strip()
    else:
        raise ValueError("Bad mode %r" % (mode))


def docker_get_containers(name):
    containers = docker_output(
        ["ps", "-a", "-q", "--filter",
         "name=%s" % (name)], mode="lines")
    return containers
