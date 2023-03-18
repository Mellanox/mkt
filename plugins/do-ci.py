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
    subprocess.check_call(["git", "config", "--global",
                           "--add", "safe.directory", args.src])
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
    is_include_was_changed = False
    for f in files:
        if f.startswith(supported):
            dirlist.add(os.path.join(os.path.dirname(f), ''))
        if f.startswith("include"):
            is_include_was_changed = True

    args.filter_by_diff = False
    if not dirlist and is_include_was_changed:
        # Let's do smart guess and try to check subsystems,
        # which we are changing most of the time.
        dirlist.add("drivers/infiniband/")
        dirlist.add("drivers/net/ethernet/mellanox/")
        dirlist.add("net/")
        dirlist.add("drivers/nvme/")
        args.filter_by_diff = True

    args.dirlist = list(dirlist)
    args.files = files

def print_filtered_output(args, out):
    # sparse output everything on stderr
    for line in out.stderr.split('\n'):
        l = line.split(":")
        try:
            if l[0] not in args.files:
                continue
            if not l[1].isdigit():
                continue
        except IndexError:
            if not l:
                print(line)
            continue
        blame = subprocess.check_output(["git", "blame", l[0], "-L%s,%s" %(l[1], l[1]), "-l", "-s"])
        blame = blame.split()[0]
        if args.rev == blame:
            print(line)

def smatch_and_sparse(args, tool):
    if tool == "smatch":
        tool_cmd = ["CHECK=/opt/smatch/bin/smatch -p=kernel --data=/opt/smatch/share/smatch/smatch_data/",
                "C=2"]
    if tool == "sparse":
        tool_cmd = ["CHECK=sparse", "C=2", "CF='-fdiagnostic-prefix -D__CHECK_ENDIAN__'"]

    base_cmd = ["make", "-j", str(args.num_jobs), "-s"]
    subprocess.call(base_cmd + ["clean"])
    subprocess.call(base_cmd + ["allyesconfig"])
    cmd = base_cmd + tool_cmd + args.dirlist
    if args.show_all:
        subprocess.run(cmd)
        return

    out = subprocess.run(cmd, encoding='utf-8', capture_output=True)
    if args.filter_by_diff:
        subprocess.check_call(["git", "reset", "--hard", "-q", args.rev.decode() + "~1"])
        subprocess.call(base_cmd + ["clean"])
        subprocess.call(base_cmd + ["allyesconfig"])

        pre = subprocess.run(cmd, encoding='utf-8', capture_output=True)
        diff = list(set(out.stderr.split('\n')) - set(pre.stderr.split('\n')))
        # Restore
        subprocess.check_call(["git", "reset", "--hard", "-q", args.rev])
        for line in diff:
            print(line)
    else:
        print_filtered_output(args, out)

def clang(args):
    base_cmd = ["make", "-j", str(args.num_jobs), "-s", "CC=clang"]
    subprocess.call(base_cmd + ["clean"])
    subprocess.call(base_cmd + ["allyesconfig"])
    cmd = base_cmd + args.dirlist
    subprocess.call(cmd);

def checkpatch(args):
    cmd = ["%s/scripts/checkpatch.pl" %(args.checkpatch_root_dir), "-q", "--no-summary", "-g", args.rev, "--max-line-length=80", "--codespell"]
    if args.project != "kernel":
        cmd += ["--no-tree", "--ignore", "PREFER_KERNEL_TYPES,FILE_PATH_CHANGES,EXECUTE_PERMISSIONS,USE_NEGATIVE_ERRNO,CONST_STRUCT"]

    if args.gerrit:
        cmd += ["--ignore", "GERRIT_CHANGE_ID,FILE_PATH_CHANGES"]
    subprocess.call(cmd);

def warnings(args, arch=None):
    base_cmd = ["make", "-j", str(args.num_jobs), "-s"]
    # Default arch is x64
    if arch is not None:
        base_cmd = base_cmd + ["ARCH=%s" %(arch)]

    subprocess.call(base_cmd + ["clean"])
    subprocess.call(base_cmd + ["allyesconfig"])
    cmd = base_cmd + ["W=1"] + args.dirlist
    yes = subprocess.run(cmd, encoding='utf-8', capture_output=True)

    subprocess.call(base_cmd + ["clean"])
    subprocess.call(base_cmd + ["allnoconfig"])
    no = subprocess.run(cmd, encoding='utf-8', capture_output=True)

    subprocess.call(base_cmd + ["clean"])
    subprocess.call(base_cmd + ["allmodconfig"])
    mod = subprocess.run(cmd, encoding='utf-8', capture_output=True)

    for line in yes.stderr.split('\n'):
        if line.startswith("scripts") or line == '':
            # Fixup to https://lore.kernel.org/lkml/1521810279-6282-3-git-send-email-yamada.masahiro@socionext.com/
            continue
        print(line)
    for line in no.stderr.split('\n'):
        if line in yes.stderr.split('\n'):
            continue
        if line.startswith("scripts") or line == '':
            continue
        print(line)
    for line in mod.stderr.split('\n'):
        if line in yes.stderr.split('\n'):
            continue
        if line in no.stderr.split('\n'):
            continue
        if line.startswith("scripts") or line == '':
            continue
        print(line)

def setup_from_pickle(args, pickle_params):
    """The script that invokes docker passes in some more detailed parameters
    about the environment in a pickle and we adjust the configuration
    accordingly"""
    p = pickle.loads(base64.b64decode(pickle_params))
    args.src = p.get("src", None)
    args.project = p.get("project", None)
    args.rev = p.get("rev", 'HEAD')
    args.checkpatch = p.get("checkpatch", True)
    args.checkpatch_root_dir = p.get("checkpatch_root_dir", None)
    args.sparse = p.get("sparse", True)
    args.gerrit = p.get("gerrit", True)
    args.show_all = p.get("show_all", False)
    args.warnings = p.get("warnings", True)
    args.smatch = p.get("smatch", True)
    args.clang = p.get("clang", True)

def kernel_ci(args):
    if args.checkpatch:
        checkpatch(args)
    build_dirlist(args)
    if args.dirlist:
        if args.sparse:
            smatch_and_sparse(args, "sparse")
        if args.warnings:
            warnings(args)
            warnings(args, "i386")
        if args.smatch:
            smatch_and_sparse(args, "smatch")
        if args.clang:
            clang(args)

def rdma_core_ci(args):
    if args.checkpatch:
        checkpatch(args)

def iproute2_ci(args):
    if args.checkpatch:
        checkpatch(args)

parser = argparse.ArgumentParser(description='CI container')
args = parser.parse_args()

args.num_jobs = len(os.sched_getaffinity(0)) * 2
pickle_data = os.environ.get("CI_PICKLE")
setup_from_pickle(args, pickle_data)
fork(args)

if args.project == "kernel":
    kernel_ci(args)

if args.project == "rdma-core":
    rdma_core_ci(args)

if args.project == "iproute2":
    iproute2_ci(args)
