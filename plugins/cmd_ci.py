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
    parser.add_argument(
        "--no-checkpatch",
        action="store_false",
        dest="checkpatch",
        help="Skip checkpatch check",
        default=True)
    parser.add_argument(
        "--rev",
        nargs=1,
        default=['HEAD'],
        help="Commit to check")
    parser.add_argument(
        "--no-sparse",
        action="store_false",
        dest="sparse",
        help="Skip sparse check",
        default=True)
    parser.add_argument(
        "--no-ignore-gerrit",
        action="store_false",
        dest="gerrit",
        help="Ensure that gerrit trash is not in the patch",
        default=True)
    parser.add_argument(
        "--show-all",
        action="store_true",
        dest="show_all",
        help="Show all errors and not only introduced in specific commit",
        default=False)
    parser.add_argument(
        "--no-extra-warnings",
        action="store_false",
        dest="warnings",
        help="Skip W=1 compilation",
        default=True)
    parser.add_argument(
        "--no-smatch",
        action="store_false",
        dest="smatch",
        help="Skip smatch checks",
        default=True)
    parser.add_argument(
        "--no-clang",
        action="store_false",
        dest="clang",
        help="Skip CLANG checks",
        default=True)

def cmd_ci(args):
    """Local continuous integration check."""
    from . import cmd_images
    section = utils.load_config_file()
    if not args.project:
        set_args_project(args, section)

    build = Build(args.project)
    build.pickle['checkpatch'] = args.checkpatch
    build.pickle['sparse'] = args.sparse
    build.pickle['gerrit'] = args.gerrit
    build.pickle['show_all'] = args.show_all
    build.pickle["warnings"] = args.warnings
    build.pickle["smatch"] = args.smatch
    build.pickle["clang"] = args.clang

    # FIXME: allow git revisions as input to --rev.
    # But for now, let's give an option to provide
    # commit.
    build.pickle['rev'] = args.rev[0]
    do_cmd = ["python3", "/plugins/do-ci.py"]
    docker_exec(["run"] + build.run_ci_cmd(cmd_images.default_os) + do_cmd)
