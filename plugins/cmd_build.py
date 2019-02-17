"""Build sources to remove dependencies from host
"""
import os
import utils
from utils.build import *

def args_build(parser):
    parser.add_argument(
        "project",
        nargs='?',
        choices=build_list(),
        help="Project to build")
    parser.add_argument(
        "--clean",
        action="store_true",
        help=
        "Clean source code",
        default=False)
    parser.add_argument(
        '--run-shell',
        action="store_true",
        default=False,
        help="Run a shell inside the container instead of invoking build script")
    parser.add_argument(
        '--build-recipe', help="File with build recipe")

def cmd_build(args):
    """Smart build."""
    from . import cmd_images
    section = utils.load_config_file()
    if not args.project:
        set_args_project(args, section)

    build = BuildSrc(args.project)

    recipe_dir = None
    if args.build_recipe is not None:
        args.build_recipe = os.path.realpath(args.build_recipe)
        recipe_dir = os.path.dirname(args.build_recipe)

    if args.run_shell:
        do_cmd = ["/bin/bash"]
    else:
        if args.build_recipe:
            do_cmd = ["/bin/bash", args.build_recipe]
        else:
            do_cmd = build.do_cmd(args.clean)

    docker_exec_run(build.run_build_cmd(cmd_images.default_os, recipe_dir) + do_cmd)
