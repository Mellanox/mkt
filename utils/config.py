# Authors:
#   Leon Romanovsky <leonro@mellanox.com>
import os
import socket
import configparser
import pwd
import grp

host = socket.gethostname()
config_f = os.path.expanduser(
    "~/.config/mellanox/mkt/hv-%s.mkt" % (host))
if not os.path.isfile(config_f):
    # Let's try to set config from parent VM, maybe we are in nested VM
    config_f = os.path.expanduser(
        "~/.config/mellanox/mkt/hv-%s.mkt" % ('-'.join(host.split('-')[:-1])))

config = configparser.ConfigParser(allow_no_value=True)

def username():
    return pwd.getpwuid(os.getuid())[0]


def group():
    return grp.getgrgid(os.getgid())[0]


try:
    config.read(config_f)
    # Fix naming error, where we gave to "kernel" folder "linux" as the alias
    try:
        config["defaults"]['kernel'] = config["defaults"]['linux']
    except KeyError:
        pass
except configparser.MissingSectionHeaderError:
    exit(config_f + " in wrong format. Exiting ..")


def load_config_file():
    try:
        return config["defaults"]
    except KeyError:
        return dict()

def init_config_file():
    config.read(config_f)
    try:
        config.add_section("defaults")
        # new setup, set defaults
        config["defaults"] = {
            'src': '/images/' + username() + '/src/',
            'kernel': '/images/' + username() + '/src/kernel/',
            'rdma-core': '/images/' + username() + '/src/rdma-core/',
            'iproute2': '/images/' + username() + '/src/iproute2/',
            'logs': '/images/' + username() + '/logs/',
            'ccache': '/images/' + username() + '/ccache/',
        }
    except configparser.DuplicateSectionError:
        pass

    # Python 3.2+
    os.makedirs(os.path.dirname(config_f), exist_ok=True)
    with open(config_f, 'w') as f:
        config.write(f)


def get_images(name=None):
    if name:
        return config[name]

    images = []

    for I in config.keys():
        if I in ('DEFAULT', 'defaults'):
            continue
        images.append(I)

    return images

runtime_logs_dir = None

def init_log_dir(cmd):
    from datetime import datetime

    global runtime_logs_dir
    try:
        logs = config["defaults"]['logs']
    except KeyError:
        logs = "/tmp/"

    d = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
    runtime_logs_dir = logs + cmd + "/" + d + "/"
    os.makedirs(runtime_logs_dir, exist_ok=True)
