"""Compile various projects for different architectures
"""
import os
from utils.config import load
import subprocess
import tempfile
import shutil
import re
from utils.cmdline import *


def args_make(parser):
    parser.add_argument(
        "--no-pull",
        dest="pull",
        action="store_false",
        help="Do not update the base image",
        default=True)
    """ We use 0-day cross-compile list and the ist
        of supported architectures is taken from
        https://raw.githubusercontent.com/intel/lkp-tests/master/sbin/make.cross
        at 17/07/2018 """
    parser.add_argument(
        "arch",
        nargs='?',
        help="Architecture to compile",
        choices=sorted([
            "i386", "x86_64", "alpha", "arm", "arm64", "avr32", "blackfin",
            "c6x", "cris", "frv", "h8300", "hexagon", "ia64", "m32r", "m68k",
            "microblaze", "mips", "mn10300", "openrisc", "parisc", "powerpc",
            "s390", "score", "sh", "sh64", "sparc", "sparc32", "sparc64",
            "tile", "tilepro", "tilegx", "um", "unicore32", "xtensa"
        ]))
    parser.add_argument(
        "gcc",
        nargs='?',
        choices=sorted([
            "4.9.0", "4.9.1", "4.9.3", "4.9.4", "5.3.0", "5.3.0", "5.4.0",
            "5.5.0", "6.0.0", "6.2.0", "6.4.0", "7.2.0", "7.3.0", "7.3.1",
            "8.1.0"
        ]),
        help="GCC version to use")
    parser.add_argument("--dot-config", dest="file", help="Path to .config")


def cmd_make(args):
    """Compile project for different architectures."""
    check_not_root()
    section = load()

    # FIXME: It can be done with add_argument_group()
    if ((args.gcc is None and args.arch is not None)
            or (args.gcc is not None and args.arch is None)):
        exit("Please provide both GCC version and ARCH for cross-compile.")

    cmd = [
        "sudo", "docker", "run", "-t", "--tmpfs", "/build:exec", "--rm", "-v",
        section['linux'] + ":/kernel:ro", "-v", section['ccache'] + ":/ccache"
    ]

    f = tempfile.mkdtemp()
    if args.file is not None:
        if os.path.isfile(args.file):
            shutil.copy(args.file, str(f) + "/.config")
            if args.gcc is None:
                # Try to guess GCC and ARCH
                c = open(args.file)
                line = re.findall("^.*Compiler.*$", c.read(), re.MULTILINE)
                try:
                    gcc = line[0].split(' ')[4]
                    arch = line[0].split(' ')[2].split('-')[0]
                    # The x86_64 builds don't have arch embedded in, so generate
                    # IndexError for them
                    line[0].split(' ')[2].split('-')[1]
                    if arch is not "x86_64":
                        # Don't autogess for x86_64, use latest avaialble in docker
                        args.gcc = gcc
                        args.arch = arch
                except IndexError:
                    # Auto guesssing failed
                    pass
        else:
            exit("Can't find provided dot-config.")
    else:
        if os.path.isfile(section['linux'] + "/.config"):
            shutil.copy(section['linux'] + "/.config", str(f) + "/.config")
        else:
            dirname, filename = os.path.split(os.path.abspath(__file__))
            shutil.copy(dirname + "../docker/kbuild/configs/min-config",
                        str(f) + "/.config")

    cmd += ["-v", str(f) + "/:/configs/"]

    cmd += ["kbuild", "--git", "/kernel"]
    if args.gcc is not None:
        cmd += ["--gcc", args.gcc, "--arch", args.arch]

    subprocess.check_call(cmd)
    shutil.rmtree(str(f))
