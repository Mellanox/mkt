"""Build sources to remove dependencies from host
"""
import os
import utils
from utils.docker import *
import inspect
import pickle
import base64

section = utils.load_config_file()

class Build(object):
    def  __init__(self, project):
        self.src = section.get(project, None)
        self.project = project
        self.entry = ["/bin/bash", "-c"]
        # Take into acount affinity, but blindly assume
        # that we can run "2 threads per-CPU".
        self.num_jobs = len(os.sched_getaffinity(0)) * 2

    def _get_pickle(self):
        p = dict()
        p["project"] = self.project
        p["src"] = self.src
        p["rev"] = 'HEAD'

        return base64.b64encode(pickle.dumps(p)).decode()

    def factory(project):
        if project == "kernel": return KernelBuild(project);
        if project == "iproute2": return Iproute2Build(project);
        if project == "rdma-core": return RdmaCoreBuild(project);

    factory = staticmethod(factory)
    def do_cmd(self, clean=None):
        if clean:
            return self._clean()
        return self._in_place()

    def _run_cmd(self, supos, build_recipe, image_name):
        ccache = section.get('ccache', None)
        docker_os = section.get('os', supos)
        cmd = ["--rm", "-v", self.src + ":" + self.src + ":rw", "-it"]
        if build_recipe:
            cmd += ["-v", "%s:%s:ro" % (build_recipe, build_recipe)]
        if ccache:
            cmd += ["-v", ccache + ":/ccache"]

        return cmd + ["-w", self.src, make_image_name(image_name, docker_os)]

    def run_build_cmd(self, supos, build_recipe=None):
        return self._run_cmd(supos, build_recipe, "build")

    def run_ci_cmd(self, supos):
        src_dir = os.path.dirname(
                       os.path.abspath(inspect.getfile(inspect.currentframe()) + "/../"))
        cmd = ["-v", "%s/plugins/:/plugins:ro" %(src_dir)]
        cmd += ["--tmpfs", "/build:rw,exec,nosuid,mode=755,size=10G"]
        cmd += ["-e", "CI_PICKLE=%s" % (self._get_pickle())]

        return cmd + self._run_cmd(supos, None, "ci")

    def rpm(self):
        """Build RPM from source"""
        pass
    def deb(self):
        """Build DEB from source"""
        pass
    def for_install(self):
        """Compile this source in a way suitable to create runnable container"""
        pass

class KernelBuild(Build):
    def _clean(self):
        return self.entry + ["make clean"]
    def _in_place(self):
        print("Start kernel compilation in silent mode")
        ccache = section.get('ccache', None)
        if ccache:
            return self.entry + ["export CCACHE_DIR=/ccache && make CC=\"ccache gcc\" -j%d -s" % (self.num_jobs)]
        return self.entry + ["make -j%d -s" % (self.num_jobs)]

class Iproute2Build(Build):
    def _clean(self):
        return self.entry + ["make distclean"]
    def _in_place(self):
        return self.entry + ["make -j%d" % (self.num_jobs)]

class RdmaCoreBuild(Build):
    def _clean(self):
        return self.entry + ["rm -rf build"]
    def _in_place(self):
        return self.entry + ["./build.sh"]

def BuildSrc(project):
    for b in Build.__subclasses__():
        return b.factory(project)
    raise ValueError

project_marks = {
        "libibverbs": "rdma-core",
        "rdma": "iproute2",
        "kernel": "kernel",
}

def build_list():
    return sorted(project_marks.values())

def set_args_project(args, section):
    """Look in the local folder to determine
    what we were requested to build"""

    for key, value in project_marks.items():
        if os.path.isdir(key):
            args.project = value

    if not args.project:
        exit("Failed to understand the source of this directory, " +
             "don't know how to build. Exciting...")

    section[args.project] = os.getcwd()
