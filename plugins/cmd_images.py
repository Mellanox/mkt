"""Build docker images for different architectures and OS
"""
import os
import utils
from utils.git import *
from utils.docker import *
from utils.cmdline import *
from subprocess import call, Popen

supported_os = {
    "fc33",
}
default_os = next(iter(supported_os))

def get_proxy_arg(run=False):
    res = []
    if os.path.exists("/etc/apt/apt.conf.d/01proxy"):
        # The line in this file must be 'Acquire::http { Proxy "http://xxxx:3142"; };'
        with open("/etc/apt/apt.conf.d/01proxy") as F:
            proxy = F.read().strip().split('"')[1]
            if run:
                res.append("-e")
            else:
                res.append("--build-arg")
            res.append('http_proxy=%s' % (proxy))
    return res


def do_pull(dockerfn):
    """This is like docker build --pull but it only pulls things that come
    from the public docker repositories, it does not indiscriminately pull
    other things"""
    images = set()
    with open(dockerfn, "rt") as F:
        for ln in F:
            if ln.startswith("FROM"):
                name = ln.split()[-1]
                if (name.startswith("fedora") or name.startswith("ubuntu")
                        or name.startswith("centos")):
                    images.add(name)
    return images


class SupportImage(object):
    """Support images are docker images that exist only to compile from source for
    another container. We continue to use docker images for this purpose as
    docker provides a stable and reproducible environment for the build and a
    caching system to make development run faster.

    Images produces this way should have their output included in the file
    image via a COPY --from directive"""
    cdir = None

    def __init__(self, osname, script):
        if SupportImage.cdir is None:
            SupportImage.cdir = get_cache_fn("")

        self.name = re.match(r"support-(.*)\.sh", script).group(1)
        self.script = script
        self.docker_tag = make_local_image_name("support_%s" % (self.name),
                                                osname)

        # The script starts with a yaml meta-data header in bash comments
        with open(script, "rb") as F:
            ln = iter(F)
            text = []
            for I in ln:
                if I == b"# ---\n":
                    text.append(I[2:])
                    break
            else:
                raise ValueError("Bad script %r, missing header" % (script))
            for I in ln:
                if not I.startswith(b"# "):
                    break
                text.append(I[2:])
            else:
                raise ValueError("Bad script %r, mising trailer" % (script))
        import yaml
        self.spec = yaml.safe_load(b"".join(text))
        self.git_modules = False
        if ("git_modules" in self.spec):
            self.git_modules = True

    def _fetch_git(self):
        """Make sure that the required commit ID is available under ~/.cache/ for
        later use, fetching the git repo if necessary"""

        git_url = self.spec["git_url"].rstrip('/')
        git_ref = self.spec["git_commit"]

        # FIXME: We could look in the config file for an existing local git
        # repo for the project..

        self.git_dir = os.path.join(SupportImage.cdir,
                                    os.path.basename(git_url))
        if not self.git_dir.endswith(".git"):
            self.git_dir = self.git_dir + ".git"
        if not os.path.exists(self.git_dir):
            try:
                cmd = ["clone"]
                if not self.git_modules:
                    cmd += ["--bare"]
                git_call(cmd + [git_url, self.git_dir])
            except subprocess.CalledProcessError:
                shutil.rmtree(self.git_dir)

        if not self.git_modules:
            with in_directory(self.git_dir):
                print(self.git_dir)
                self.git_id = git_commit_id(git_ref, fail_is_none=True)
                if self.git_id is None:
                    git_call(["fetch", "--tags", git_url])
                    self.git_id = git_commit_id(git_ref)
        else:
            with in_directory(self.git_dir):
                git_call(["fetch"])
                self.git_id = git_commit_id(git_ref)
                git_call(["checkout", self.git_id ])
                git_call(["submodule", "update", "--init", "--recursive"])


    def _fetch_nfs(self):
        """This is very annoying but we need some files from NFS. If the system is on
        the mellanox network then just copy them from NFS, otherwise sftp them over and
        cache them."""
        self.nfs_paths = {}
        for nfs_fn, inf in self.spec.get("nfs_files", {}).items():
            if os.path.exists(nfs_fn):
                self.nfs_paths[nfs_fn] = nfs_fn
                continue

            cache_fn = "".join(
                c if re.match(r'\w', c) else '_' for c in nfs_fn)
            cache_fn = os.path.join(SupportImage.cdir, cache_fn)
            self.nfs_paths[nfs_fn] = cache_fn
            if os.path.exists(cache_fn):
                continue

            # FIXME: This just uses Jason's lab server for lack of something better..
            tmp_fn = cache_fn + ".tmp"
            subprocess.check_call(
                ["sftp",
                 "gen-l-vrt-197.mtl.labs.mlnx:%s" % (nfs_fn), tmp_fn])
            os.rename(tmp_fn, cache_fn)

    def fetch(self):
        """Retrieve any outside materials for this image build"""
        if "git_commit" in self.spec:
            self._fetch_git()
        if "nfs_files" in self.spec:
            self._fetch_nfs()

    def _make_docker_file(self, dockerfn):
        """All docker files for building support images start with the same preamble,
        docker will cache this across the builds."""
        with open(dockerfn, "wt") as FO:
            with open("support.Dockerfile", "rt") as FI:
                for ln in FI:
                    FO.write(ln)
            subst = {
                "tarfn": os.path.basename(self.tarfn),
                "script": self.script,
            }
            for image_tag, inf in self.spec.get("image_files", {}).items():
                for I in inf["files"]:
                    FO.write(
                        "COPY --from=%s %s %s\n" % (image_tag, I, inf["dest"]))
            for nfs_fn, inf in self.spec.get("nfs_files", {}).items():
                FO.write(
                    "ADD %s %s\n" % (os.path.basename(nfs_fn), inf["dest"]))
            FO.write("ADD {tarfn} /\n".format(**subst))
            FO.write(
                "RUN mkdir -p /opt/src && cd /opt/src/ && /bin/bash -e /opt/{script}".
                format(**subst))

    def _setup_git(self, dfn):
        with in_directory(self.git_dir):
            if not self.git_modules:
                git_call([
                    "archive", "--format=tar", "--prefix", "opt/src/", "-o",
                    self.tarfn, self.git_id
                ])
            else:
                subprocess.check_call([
                    "tar", "--create", "--mtime=Jan 1 2010", "--file", self.tarfn,
                    "--transform", "s|^|opt/src/|", "."])
#                    "--exclude", ".git", "--transform", "s|^|opt/src/|", "."])

    def _setup_nfs(self, dfn):
        for nfs_fn, inf in self.spec.get("nfs_files", {}).items():
            shutil.copy(self.nfs_paths[nfs_fn],
                        os.path.join(dfn, os.path.basename(nfs_fn)))

    def _setup_script(self):
        """Bundle the support files into the tar file so we only create one docker
        layer.  This is done with a stable timestamp so that the tar file
        content is identical if it does not change."""
        all_files = [self.script]
        all_files.extend(self.spec.get("other_files", []))

        if os.path.exists(self.tarfn):
            subprocess.check_call([
                "tar", "--append", "--mtime=Jan 1 2010", "--file", self.tarfn,
                "--transform", "s|^|opt/|"
            ] + all_files)
        else:
            subprocess.check_call([
                "tar", "--create", "--mtime=Jan 1 2010", "--file", self.tarfn,
                "--transform", "s|^|opt/|"
            ] + all_files)

    def build_image(self, osname, build_cmd):
        with tempfile.TemporaryDirectory() as dfn:
            self.tarfn = self.name + ".tar"
            self.tarfn = os.path.join(dfn, self.tarfn)

            if "git_commit" in self.spec:
                self._setup_git(dfn)
            if "nfs_files" in self.spec:
                self._setup_nfs(dfn)
            self._setup_script()

            self._make_docker_file(os.path.join(dfn, "Dockerfile"))

            docker_call(build_cmd + ["-t", self.docker_tag, dfn])

    def get_depends(self):
        """Return a list of image tags or short names that this image depends on to
        build."""
        for image_tag, inf in self.spec.get("image_files", {}).items():
            yield image_tag


def load_supported(args):
    """Read the support module scripts from the os directory"""
    supported = {}
    for fn in os.listdir():
        if fn.startswith("support-") and fn.endswith(".sh"):
            img = SupportImage(args.os, fn)
            supported[img.name] = img
    imgs = [img for _, img in sorted(supported.items())]
    for I in list(supported.values()):
        supported[I.docker_tag] = I

    def add_elm(img):
        """Topological sorting helper"""
        if img.name in done:
            return
        done.add(img.name)
        for I in sorted(img.get_depends()):
            add_elm(supported[I])
        res.append(img)

    done = set()
    res = []
    for I in imgs:
        add_elm(I)
    return res


def args_images(parser):
    parser.add_argument(
        "--no-pull",
        dest="pull",
        action="store_false",
        help=
        "Do not update the base docker images from the public docker registry",
        default=True)

    parser.add_argument(
        "--only",
        action="store",
        help="Build only the image with the given docker image tag",
        default=None)

    parser.add_argument(
        "--push",
        action="store_true",
        help=
        "Upload created images to docker registry (need to have an account in harbor registry)",
        default=False)

    section = utils.load_config_file()
    parser.add_argument(
        "os",
        nargs='?',
        help="The image to build",
        choices=sorted(supported_os),
        default=section.get('os', default_os))


def cmd_images(args):
    """Build docker images for different architectures and OS."""

    if args.push:
        docker_call(["login", docker_registry_name()])

    with in_directory(utils.get_internal_fn(os.path.join("docker", args.os))):
        images = (
            (make_image_name("build", args.os), "support.Dockerfile"),
            (make_image_name("kvm", args.os), "kvm.Dockerfile"),
            (make_image_name("ci", args.os), "ci.Dockerfile"),
        )
        if args.pull:
            to_pull = set()
            for image, dockerfn in images:
                to_pull.update(do_pull(dockerfn))
            for I in to_pull:
                docker_call(["pull", I])

        support = load_supported(args)
        for I in support:
            I.fetch()

        cmd = ["build"] + get_proxy_arg()
        for I in support:
            if args.only is not None and not I.docker_tag.startswith(args.only):
                continue

            print("------- Building support image %s -------" % (I.docker_tag))
            I.build_image(args.os, cmd)

        for image, dockerfn in images:
            if image is None :
                continue

            if args.only is not None and not image.startswith(args.only):
                continue

            docker_call(cmd + ["-t", image, "-f", dockerfn, "."])
            if args.push:
                docker_call(["push", image])
