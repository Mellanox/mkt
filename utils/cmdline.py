# Authors:
#   Jason Gunthorpe <jgg@mellanox.com>

import argparse
import importlib
import inspect
import sys
import os
import functools
import subprocess
import shlex
import utils

source_root = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
cache_dir = None


def get_internal_fn(fn):
    """Return the full path to an internal file. When running "in-place" this path
    points into the source directory"""
    return os.path.join(source_root, fn)


def get_cache_fn(fn):
    """Return a 'cache' filename. Cache files are ones that can be deleted without
    an impact on the operation of mkt - at worst it will run slower."""
    global cache_dir
    if cache_dir is None:
        cache_dir = os.path.expanduser("/global/home/users/artemp/scratch/.cache/mellanox/mkt/")
        # In MTL network, user home directories are located on /labhome
        # and doesn't have enough space to build cache efficiently.
        # Do nasty hack and replace labhome with swgwork
        if not os.path.exists(cache_dir):
            scache_dir = cache_dir.replace('labhome', 'swgwork')
            if cache_dir != scache_dir:
                os.makedirs(scache_dir, exist_ok=True)
                os.makedirs(os.path.expanduser("~/.cache/mellanox/") , exist_ok=True)
                subprocess.check_call(["ln", "-s", scache_dir, cache_dir[:-1]])
            else:
                os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, fn)


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write(
                "Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def load_all_commands(name, top_module):
    """Load the modules containing the command implementation and then extract all
    the cmd_* functions from them."""
    module = importlib.import_module(top_module.__name__ + "." + name)
    for k in dir(module):
        fn = getattr(module, k)
        argsfn = getattr(module, "args_" + k[4:], None)
        if (argsfn is None or not k.startswith("cmd_")
                or not inspect.isfunction(fn)):
            continue
        yield (k, fn, argsfn)


def my_print_help(cmd_fn_name, fallback_fn, file=None):
    """If the command has a manual page in the doc directory then
    display that instead of the --help output"""
    pd_fn = get_internal_fn("docs/mkt_%s.1.md" % (cmd_fn_name[4:]))
    if not os.path.exists(pd_fn) or "MKT_PYTHON_HELP" in os.environ:
        return fallback_fn(file)

    try:
        subprocess.check_output(
            ["bash", "-c", "pandoc --version"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        subprocess.check_call(["less", pd_fn])
        return

    subprocess.check_call([
        "bash", "-c",
        "pandoc -s -t man %s | man -l -" % (shlex.quote(pd_fn))
    ])


def check_not_root():
    if not os.getuid():
        exit("Please don't run this program as root")


def main(cmd_modules, top_module):
    parser = argparse.ArgumentParser(description="""Mellanox Kernel Toolset

Various utilities for working with the Linux kernel at Mellanox""")
    subparsers = parser.add_subparsers(title="Sub commands", dest="command")
    subparsers.required = True

    commands = []
    for I in cmd_modules:
        commands.extend(load_all_commands(I, top_module))
    commands.sort()

    # build sub parsers for all the loaded commands
    for k, fn, argsfn in commands:
        sparser = subparsers.add_parser(
            k[4:].replace('_', '-'), help=fn.__doc__)
        sparser.required = True
        argsfn(sparser)
        sparser.set_defaults(func=fn)
        sparser.print_help = functools.partial(my_print_help, k,
                                               sparser.print_help)

    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    # argparse will set 'func' to the cmd_* that executes this command
    args = parser.parse_args()
    check_not_root()
    utils.init_log_dir(args.command)
    args.func(args)
