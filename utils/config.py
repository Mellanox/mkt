# Authors:
#   Leon Romanovsky <leonro@mellanox.com>
import os
import socket
import configparser
import pwd
import grp

config_f = os.path.expanduser('~') + '/.x-tools/' + socket.gethostname() + '.xt';
config = configparser.ConfigParser(allow_no_value=True);

username = pwd.getpwuid( os.getuid() )[ 0 ];
group = grp.getgrgid( os.getgid() )[ 0 ];

try:
    config.read(config_f);
except configparser.MissingSectionHeaderError:
    exit(config_f + " in wrong format. Exiting ..");

def load():
    try:
        return config["defaults"];
    except KeyError:
        exit(socket.gethostname() + ' machine doesn\'t exist in ~/.x-tools/.\nPlease run setup before. Exiting ...');

def init():
    config.read(config_f);
    try:
        config.add_section("defaults");
        # new setup, set defaults
        config["defaults"] = { 'src': '/images/' + username + '/src/',
                              'linux': '/images/' + username + '/src/kernel/',
                              'rdma-core': '/images/' + username + '/src/rdma-core/',
                              'iproute2': '/images/' + username + '/src/iproute2/',
                              'logs': '/images/' + username + '/logs/',
                              'ccache': '/images/' + username + '/ccache/',
                              'os': 'fc28'};
    except configparser.DuplicateSectionError:
        pass

    # Python 3.2+
    os.makedirs(os.path.dirname(config_f), exist_ok=True)
    with open(config_f, 'w') as f:
        config.write(f);

def get_images(name=None):

    if name:
        return config[name];

    images = [];

    for I in config.keys():
        if I in ('DEFAULT', 'defaults'):
            continue;
        images.append(I);

    return images;
