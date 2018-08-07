# Authors:
#   Jason Gunthorpe <jgg@mellanox.com>

import argparse
import importlib
import inspect
import sys
import os


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

    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    # argparse will set 'func' to the cmd_* that executes this command
    args = parser.parse_args()
    args.func(args)


def check_not_root():
    if not os.getuid():
        exit("Please don't run this program as root")
