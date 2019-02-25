"""Build sources to remove dependencies from host
"""
import os
import utils
from utils.docker import *
import inspect
import pickle
import base64
from utils.config import username, group

section = utils.load_config_file()

class Build(object):
    def  __init__(self, project):
        self.src = section.get(project, None)
        self.project = project
        self.pickle = dict()

    def _get_pickle(self):
        self.pickle["project"] = self.project
        self.pickle["src"] = self.src

        return base64.b64encode(pickle.dumps(self.pickle)).decode()

    def _run_cmd(self, supos, build_recipe, image_name):
        ccache = section.get('ccache', None)
        docker_os = section.get('os', supos)
        cmd = ["--rm", "-v", self.src + ":" + self.src + ":rw", "-it"]

        src_dir = os.path.dirname(
                       os.path.abspath(inspect.getfile(inspect.currentframe()) + "/../"))
        cmd += ["-v", "%s/plugins/:/plugins:ro" %(src_dir)]

        if build_recipe:
            cmd += ["-v", "%s:%s:ro" % (build_recipe, build_recipe)]
        if ccache:
            cmd += ["-v", ccache + ":/ccache"]

        return cmd + ["-w", self.src, make_image_name(image_name, docker_os)]

    def run_build_cmd(self, supos, build_recipe=None):
        cmd = ["-e", "BUILD_PICKLE=%s" % (self._get_pickle())]
        cmd += ["-v", "%s:%s:ro" %(os.getenv("HOME"), os.getenv("HOME"))]

        return cmd + self._run_cmd(supos, build_recipe, "build")

    def run_ci_cmd(self, supos):
        cmd = ["--tmpfs", "/build:rw,exec,nosuid,mode=755,size=10G"]
        cmd += ["-e", "CI_PICKLE=%s" % (self._get_pickle())]

        return cmd + self._run_cmd(supos, None, "ci")

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
