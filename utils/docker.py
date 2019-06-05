import subprocess
import os
import utils

def docker_registry_name():
    return "harbor.mellanox.com"

def make_image_name(thing, version):
    return docker_registry_name() + "/mkt/%s:%s" % (thing, version)

def make_local_image_name(thing, version):
    return "local_mkt/%s:%s" % (thing, version)


def docker_call(args):
    """Run docker and display the output to the terminal"""
    with open('%sdocker.cmdline' %(utils.config.runtime_logs_dir), 'w+') as f:
        f.write(" ".join(args))

    return subprocess.check_call([
        'sudo',
        'docker',
    ] + args)


def docker_exec(args):
    """Run docker and display the output to the terminal"""
    with open('%sdocker.cmdline' %(utils.config.runtime_logs_dir), 'w+') as f:
        f.write(" ".join(args))

    return os.execvp("sudo", [
        'sudo',
        'docker',
    ] + args)

def docker_output(args, mode=None):
    """Run docker and return the output"""
    with open('%sdocker.cmdline' %(utils.config.runtime_logs_dir), 'w+') as f:
        f.write(" ".join(args))

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


def docker_get_containers(label):
    containers = docker_output(
        ["ps", "--format", '"{{.Names}}"', "--filter",
         "label=%s" % (label)], mode="lines")
    return containers
