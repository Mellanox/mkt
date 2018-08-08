import os
import re
import subprocess
import tempfile
import shutil
import datetime
import collections
from contextlib import contextmanager

# Regex that matches a git object name/SHA1
IDRE = b"^[0-9a-fA-F]{40}$"


def bytes_join(*args):
    """Concatinate args together. If any of args are a bytes then the result
    will be bytes, otherwise it is str. This is useful when appending
    constant strings known to be simple characters."""
    if any(isinstance(I, bytes) for I in args):
        return b"".join(
            I if isinstance(I, bytes) else I.encode() for I in args)
    else:
        return "".join(args)


@contextmanager
def in_directory(dir):
    """Context manager that chdirs into a directory and restores the original
    directory when closed."""
    cdir = os.getcwd()
    try:
        os.chdir(dir)
        yield True
    finally:
        os.chdir(cdir)


def git_call(args):
    """Run git and display the output to the terminal"""
    return subprocess.check_call([
        'git',
    ] + args)


def git_output(args, mode=None, null_stderr=False, input=None):
    """Run git and return the output"""
    if null_stderr:
        with open("/dev/null") as F:
            o = subprocess.check_output(
                [
                    'git',
                ] + args, stderr=F, input=input)
    else:
        o = subprocess.check_output(
            [
                'git',
            ] + args, input=input)
    if mode == "raw":
        return o
    elif mode == "lines":
        return o.splitlines()
    elif mode is None:
        return o.strip()
    else:
        raise ValueError("Bad mode %r" % (mode))


def git_output_to_file(args, file):
    """Run git and send the output to a file"""
    return subprocess.check_call(
        [
            'git',
        ] + args, stdout=file)


def git_norm_id(gid):
    if not re.match(IDRE, gid):
        raise ValueError("Not a git ID %r" % (gid))
    if isinstance(gid, bytes):
        return gid.decode()
    return gid


def git_output_id(args, mode=None, input=None):
    """Same as git_output, but guarantees the result is a well formed git object ID"""
    if mode == "lines":
        return [git_norm_id(I) for I in git_output(args, mode, input=input)]
    return git_norm_id(git_output(args, mode, input=input))


def git_ref_id(thing, fail_is_none=False):
    """Return the git ID for a ref or None"""
    try:
        o = git_output(["rev-parse", thing], null_stderr=True)
    except subprocess.CalledProcessError:
        if fail_is_none:
            return None
        raise
    return git_norm_id(o)


def git_commit_id(thing, fail_is_none=False):
    """Returns a commit ID for thing. If thing is a tag or something then it is
    converted to a object ID"""
    return git_ref_id(
        bytes_join(thing, "^{commit}"), fail_is_none=fail_is_none)


def git_root():
    """Return the top of the source directory we are currently in"""
    res = git_output(
        [
            "rev-parse",
            "--is-inside-work-tree",
            "--is-inside-git-dir",
            "--is-bare-repository",
            "--absolute-git-dir",
            "--show-cdup",  # must be last, may not print
        ],
        mode="lines")

    assert (len(res) == 5 or len(res) == 4)

    if res[0] == b"true":
        # The use of cdup and PWD means we return the path with any symlinks
        # intact.
        cwd = os.environ.get("PWD")
        if cwd is None:
            cwd = os.getcwd()
        return os.path.normpath(os.path.join(cwd, res[4].decode()))

    if res[1] == b"true":
        if res[2] == b"true":
            return res[3].decode()
        return os.path.normpath(os.path.join(res[3].decode(), ".."))
    raise ValueError("Not a git directory")


GitObject = collections.namedtuple("GitObject", "keys raw_keys desc")


def git_read_object(obj_type, idish):
    """Return the raw git internal object such as a commit or tag,
    processing out the header."""
    lines = git_output(["cat-file", obj_type, idish], mode="lines")

    # Read the key/values from the control block
    keys = []
    itr = iter(lines)
    for I in itr:
        # Indented blocks are used as part of merge commits,
        # eg the embed the signed tag
        if I.startswith(b" "):
            continue
        I = I.rstrip()
        if not I:
            break
        kv = I.partition(b' ')
        keys.append((kv[0], kv[2]))

    desc = list(I for I in itr)
    dkeys = {}
    for k, v in keys:
        k = k.decode()
        # make multi-lists into something like 'parents'
        if k in dkeys:
            ks = k + 's'
            if ks not in dkeys:
                dkeys[ks] = [dkeys[k], v]
            else:
                dkeys[ks].append(v)
        else:
            dkeys[k] = v

    return GitObject(keys=dkeys, raw_keys=keys, desc=desc)


def git_trailers(commit):
    """Return a list of trailers from a commit message"""
    res = []
    for I in git_output(
        ["show", "--no-patch", "--pretty=%(trailers:only,unfold)", commit],
            mode="lines"):
        if not I.strip():
            continue
        I = I.partition(b":")
        res.append((I[0].strip().decode(), I[2].strip()))
    return res


def extract_date(s):
    """Return the date in gmtime from an internal git date string of 1514090852 -0800"""
    g = re.match(rb".* (\d+) ([+-])(\d\d)(\d\d)", s)
    if g is None:
        raise ValueError("No git raw date in %r" % (s))
    tzoffset = datetime.timedelta(
        minutes=int(g.group(2) + b"1") *
        (int(g.group(3)) * 60 + int(g.group(4))))
    tz = datetime.timezone(tzoffset)
    return datetime.datetime.fromtimestamp(int(g.group(1)), tz)


@contextmanager
def git_temp_worktree():
    """Context manager that creates a temporary work tree and chdirs into it.  The
    worktree is deleted when the contex manager is closed"""
    with tempfile.TemporaryDirectory() as dfn:
        git_call(["worktree", "add", "--detach", "--no-checkout", dfn])
        with in_directory(dfn):
            yield


def get_remote_branches():
    """Return the name of all remote branches"""
    branches = git_output(
        ["branch", "--all", "--list", "--format", '%(refname)'], mode="lines")
    return set(I for I in branches if I.startswith(b"refs/remotes"))


class GitRange(object):
    def __init__(self, newest, ancestor):
        self.newest = git_commit_id(newest)
        self.ancestor = git_commit_id(ancestor)

    def rev_range(self):
        return [self.newest, "^" + self.ancestor]

    def get_changed_files(self):
        """Return a list of all files that are different between the two treeish
        things. This is a straight up diff between the two points"""
        diff = git_output(
            ["diff-tree", "-r", self.newest, self.ancestor], mode="lines")
        return [I.partition(b"\t")[2] for I in diff]

    def get_commit_changed_files(self):
        """Look at each commit in the range and combine the list of files it
        touches"""
        res = set()
        for I in self.get_commit_list(extra_args=["--no-merges"]):
            res.update(GitRange(I, I + "^").get_changed_files())
        return res

    def fork_gitk(self):
        """Runs gitk in the background"""
        subprocess.Popen(["gitk"] + self.rev_range(), close_fds=True)

    def get_commit_list(self, extra_args=[]):
        ids = git_output(
            ["rev-list"] + extra_args + self.rev_range(), mode="lines")
        res = []
        for I in ids:
            assert re.match(IDRE, I)
            res.append(I.decode())
        return res

    def sanity_check(self):
        """Check if the number of commits in the range is unusually high,
        this usually indicates a user error."""
        count = len(self.get_commit_list())
        if count >= 100:
            raise ValueError(
                "Too many commits (%u) between %s ^%s probably a mistake" %
                (count, self.newest, self.ancestor))


def git_base_fewest_commits(references, head="HEAD"):
    """The returns the merg base between HEAD and all the hints in references.
    This is used as part of the algorithm to automatically get a commit range
    for the work in progress."""

    # The automatic reference is all remote branches.
    if references is None:
        references = get_remote_branches()
    assert references

    # merge-base solves this problem automatically if the right bases are used
    base = git_output_id(["merge-base", head] + [I for I in references])
    return GitRange(head, base)


def establish_ko_ssh(always_prompt=False):
    """Open a session to k.o ssh that can write"""
    from . import config

    try:
        res = subprocess.check_output(
            ["ssh", config.ko_ssh_server, "2fa", "isval"])
    except subprocess.CalledProcessError as ex:
        res = ex.output

    res = res.strip()
    if res == b"True":
        if always_prompt:
            print("Press ENTER ")
            input()
        return

    if res != b"False":
        raise ValueError("Unable to communicate with k.o %r" % (res))

    # FIXME: we could use ykman oath but we have to rekey and there seems to
    # be a problem with scdaemon?
    print("Press YubiKey button for HTOP")
    keys = input()
    if not re.match(r"\d" * 6, keys):
        raise ValueError("Invalid HTOP %r" % (keys))
    subprocess.check_call(
        ["ssh", "git@gitolite.kernel.org", "2fa", "val-session", keys])


def git_push(remote, things=None, force=False):
    """Push something to k.o git. If things is None then the default push is
    performed."""

    if things is None:
        things = []
    if force:
        things = ["-f"] + things

    # Open a ssh session and sync the local branches
    git_call(["fetch", remote, "--prune"])
    git_call(["push", remote, "-n"] + things)

    establish_ko_ssh(True)
    git_call(["push", remote] + things)


def compile_test(dot_config, mfiles=None):
    """Run a compile test on a kernel tree"""
    from . import config

    make = [
        "make", "CC=" + config.compiler, "HOSTCC=" + config.compiler, "-s",
        "-j8"
    ]
    shutil.copyfile(dot_config, ".config")
    subprocess.check_call(make + ["oldconfig"])
    print(
        "Running test compile using %r and %s" % (dot_config, config.compiler))

    # If a list of modified files given then explicitly try and compile the .c
    # files in the list first. This speeds up error detection and also serves
    # to confirm we are compile testing every file we are touching as make
    # will fail if there is no rule to make the .o file.
    if mfiles is not None:
        lst = set()
        for I in mfiles:
            if I.endswith(b".c") and os.path.exists(I):
                lst.add(I[:-2] + b".o")
        subprocess.check_call(make + sorted(lst))

    subprocess.check_call(make)
