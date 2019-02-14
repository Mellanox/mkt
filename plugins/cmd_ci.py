"""Perform CI checks locally
"""
import os
import utils
from utils.build import *

def args_ci(parser):
    parser.add_argument(
        "project",
        nargs='?',
        choices=build_list(),
        help="Project to build")

def cmd_ci(args):
    """Local continuous integration check."""
    from . import cmd_images
    section = utils.load_config_file()
    if not args.project:
        set_args_project(args, section)

    build = BuildSrc(args.project)

    do_cmd = ["python3", "/plugins/do-ci.py"]
    docker_exec(["run"] + build.run_ci_cmd(cmd_images.default_os) + do_cmd)
