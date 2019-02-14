#!/usr/bin/env python3

import os
import subprocess
import pickle
import base64
import argparse
from shutil import copy

def fork(args):
    """Checkout the linux source tree into the build directory so that everything
    about the build is pristine and isolated within the container."""
    head = subprocess.check_output(["git", "rev-parse", args.rev], cwd=args.src).strip()
    obj_dir = subprocess.check_output(["git", "rev-parse", "--git-path", "objects"],
                                      cwd=args.src)
    obj_dir = os.path.join(args.src, obj_dir.decode())

    # Create an empty git repository. Native clone is too slow because the
    # typical gerrit source repo has a huge number of refs and git has to
    # inspect all of them. This approach lets us ignore all of that to only
    # use the rev we were asked to build.
    os.mkdir("/build/%s" %(args.project))
    os.chdir("/build/%s" %(args.project))
    subprocess.check_call(["git", "init", "-q"])

    # Setup alternates so we can see all the objects in the source repo
    with open(".git/objects/info/alternates", "w") as F:
        F.write(obj_dir)
        F.write("\n")

    # Create a branch using the only remote HEAD we care about
    subprocess.check_call(["git", "checkout", "-q", "-b", "build", "--no-progress", head])
    subprocess.check_call(["git", "--no-pager", "log", "--oneline", "-n1"])

    if args.project == "kernel":
        copy("%s/.config" %(args.src), "/build/%s" %(args.project))

    args.src = "/build/%s" %(args.project)

def setup_from_pickle(args, pickle_params):
    """The script that invokes docker passes in some more detailed parameters
    about the environment in a pickle and we adjust the configuration
    accordingly"""
    p = pickle.loads(base64.b64decode(pickle_params))
    args.src = p.get("src", None)
    args.project = p.get("project", None)
    args.rev = p.get("rev", 'HEAD')

parser = argparse.ArgumentParser(description='CI container')
args = parser.parse_args()

pickle_data = os.environ.get("CI_PICKLE")
setup_from_pickle(args, pickle_data)
fork(args)


subprocess.check_call(["/bin/bash"])
