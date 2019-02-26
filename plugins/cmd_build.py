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
    parser.add_argument(
        '--with-kernel-headers',
        action="store_true",
        default=False,
        help="Install kernel headers (used in custom build target)")

def cmd_build(args):
    """Smart build."""
    from . import cmd_images
    section = utils.load_config_file()
    if not args.project:
        set_args_project(args, section)

    if args.project != 'custom' and args.with_kernel_headers:
        exit("--with-kernel-headers is applicable for \"custom\" target only.")

    build = Build(args.project)

    recipe_dir = None
    if args.build_recipe is not None:
        args.build_recipe = os.path.realpath(args.build_recipe)
        recipe_dir = os.path.dirname(args.build_recipe)

    build.pickle['shell'] = args.run_shell
    build.pickle["passwd"] = "%s:x:%s:%s:%s:%s:/bin/bash" % (username(),
                os.getuid(), os.getgid(), username(), os.getenv("HOME"))
    build.pickle["group"] = "%s:x:101:" % (group())
    build.pickle["uid"] = int(os.getuid())
    build.pickle["gid"] = int(os.getgid())
    build.pickle["home"] = os.getenv("HOME")
    build.pickle['clean'] = args.clean
    build.pickle['build_recipe'] = args.build_recipe

    if args.with_kernel_headers:
        build.pickle['kernel'] = section.get('kernel', None)

    do_cmd = ["python3", "/plugins/do-build.py"]
    docker_exec(["run"] + build.run_build_cmd(cmd_images.default_os, recipe_dir) + do_cmd)
