"""Helper commands to run driver_test
"""
import os
import utils
from utils.docker import *
from . import cmd_images
from . import cmd_run


def args_drvt_gui(parser):
    section = utils.load_config_file()
    parser.add_argument(
        "--os",
        action="store",
        help="The OS image to get the GUI from",
        choices=sorted(cmd_images.supported_os),
        default=section.get('os', 'fc28'))

    parser.add_argument(
        "--topology_file",
        action="store",
        help="Pass through the topology_file argument to driver test",
        default=None)

    parser.add_argument(
        "--result_path",
        action="store",
        help="Pass through the result_path argument to driver test",
        default=None)

    parser.add_argument(
        "--devel",
        action="store",
        help=
        "Setup the given one test source directory as the source code to run the GUI. The player will continue to use its own source code.",
        default=None)

    parser.add_argument(
        "DRVT_ARGS", nargs="*", help="Arguments to pass to driver_test, place them after a --")


def cmd_drvt_gui(args):
    """Launch the driver_test GUI."""
    mapdirs = cmd_run.DirList()
    mapdirs.add("/tmp/.X11-unix")

    if args.topology_file is not None:
        fn = os.path.realpath(args.topology_file)
        assert fn.endswith(".ini")
        mapdirs.add(os.path.dirname(fn))
        args.DRVT_ARGS = ["--topology_file", fn] + args.DRVT_ARGS

    if args.result_path is not None:
        fn = os.path.realpath(args.result_path)
        assert os.path.isdir(args.result_path)
        mapdirs.add(args.result_path)
        args.DRVT_ARGS = ["--result_path", fn] + args.DRVT_ARGS

    dargs = []
    home = os.path.expanduser("~")
    if args.devel:
        assert os.path.isdir(args.devel)
        assert os.path.isdir(os.path.join(args.devel,".git"))

        dargs.extend([
            "-v",
            "%s:/usr/lib64/python2.7/site-packages/drivertest:ro" %
            (os.path.join(args.devel,"drivertest"))
        ])

    if "DISPLAY" in os.environ:
        dargs.extend(["-e","DISPLAY=%s" % (os.environ["DISPLAY"])])
        xauth = os.path.join(home,".Xauthority")
        if os.path.isfile(xauth):
            dargs.extend(["-v","%s:%s:ro"%(xauth,xauth)])

    docker_exec(["run"] + mapdirs.as_docker_bind() + dargs + [
        "--rm",
        "--tty",
        "--interactive",
        "--ipc=host",
        "--net=host",
        "--user",
        "%d:%d"%(os.getuid(), os.getgid()),
        "-e","HOME=%s"%(home),
        make_image_name("kvm", args.os),
        "/usr/bin/drivertest_gui",
        "--without_install",
    ] + args.DRVT_ARGS)


def args_drvt(parser):
    args_drvt_gui(parser)
def cmd_drvt(args):
    """Launch the driver_test terminal."""
    mapdirs = cmd_run.DirList()

    if args.topology_file is not None:
        fn = os.path.realpath(args.topology_file)
        assert fn.endswith(".ini")
        mapdirs.add(os.path.dirname(fn))
        args.DRVT_ARGS = ["--topology_file", fn] + args.DRVT_ARGS

    if args.result_path is not None:
        fn = os.path.realpath(args.result_path)
        assert os.path.isdir(args.result_path)
        mapdirs.add(args.result_path)
        args.DRVT_ARGS = ["--result_path", fn] + args.DRVT_ARGS

    dargs = []
    home = os.path.expanduser("~")
    if args.devel:
        assert os.path.isdir(args.devel)
        assert os.path.isdir(os.path.join(args.devel,".git"))

        dargs.extend([
            "-v",
            "%s:/usr/lib64/python2.7/site-packages/drivertest:ro" %
            (os.path.join(args.devel,"drivertest"))
        ])

    docker_exec(["run"] + mapdirs.as_docker_bind() + dargs + [
        "--rm",
        "--tty",
        "--interactive",
        "--net=host",
        "--user",
        "%d:%d"%(os.getuid(), os.getgid()),
        "-e","HOME=%s"%(home),
        make_image_name("kvm", args.os),
        "/usr/bin/drivertest_terminal",
        "--without_install",
    ] + args.DRVT_ARGS)

    # Useful sequences:

# mkt drvt --topology_file `/bin/pwd`/test.ini --result_path `/bin/pwd` -- --random_file /usr/lib64/python2.7/site-packages/drivertest/keeps/ib/all.yaml

# mkt drvt-gui --devel ~/mlx/onetest/ --topology_file ./test.ini -- --random_file /usr/lib64/python2.7/site-packages/onetest/DriVerTest/Keeps/IB/all.yaml
# mkt drvt-gui --topology_file /tmp/test.ini --result_path /images/jgg/results -- --random_file /usr/lib64/python2.7/site-packages/onetest/DriVerTest/Keeps/IB/all.yaml --autopilot
# mkt run mlx5_1 --dir ~ --dir /images/jgg/results
# http://veristats.mellanox.com/veristats_home/dri_ver_test_custom_run_view//swgwork/jgg/results/3/
