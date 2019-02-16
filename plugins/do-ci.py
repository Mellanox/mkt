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
    args.rev = head

def build_dirlist(args):
    files = subprocess.check_output(["git", "show", "--name-only",
        "--oneline", args.rev], cwd=args.src).decode().split('\n')
    # Remove subjet line
    files = files[1:]
    # Leave only directories which we know how to check
    supported = ("arch", "block", "crypto", "fs", "init", "ipc", "kernel",
        "lib", "mm", "drivers", "net", "security", "sound", "virt")
    dirlist = set()
    for f in files:
        if f.startswith(supported):
            dirlist.add(os.path.join(os.path.dirname(f), ''))
    args.dirlist = list(dirlist)

def sparse(args):
    subprocess.call(["make", "-j", "64", "-s", "clean"])
    subprocess.call(["make", "-j", "64", "-s", "allyesconfig"])
    subprocess.call(["make", "-j", "64", "-s", "CHECK=sparse", "C=2"] + args.dirlist)

def checkpatch(args):
    cmd = ["%s/scripts/checkpatch.pl" %(args.src), "-q", "--no-summary", "-g", args.rev]
    if args.gerrit:
        cmd += ["--ignore", "GERRIT_CHANGE_ID"]

    subprocess.call(cmd);

def setup_from_pickle(args, pickle_params):
    """The script that invokes docker passes in some more detailed parameters
    about the environment in a pickle and we adjust the configuration
    accordingly"""
    p = pickle.loads(base64.b64decode(pickle_params))
    args.src = p.get("src", None)
    args.project = p.get("project", None)
    args.rev = p.get("rev", 'HEAD')
    args.checkpatch = p.get("checkpatch", True)
    args.sparse = p.get("sparse", True)
    args.gerrit = p.get("gerrit", True)

parser = argparse.ArgumentParser(description='CI container')
args = parser.parse_args()

pickle_data = os.environ.get("CI_PICKLE")
setup_from_pickle(args, pickle_data)
fork(args)

if args.project == "kernel":
    if args.checkpatch:
        checkpatch(args)
    build_dirlist(args)
    if args.sparse:
        sparse(args)