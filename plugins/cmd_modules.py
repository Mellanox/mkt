import subprocess
import platform
import pickle
import os
import stat


class Module(object):
    dirty = False
    minfo = None

    def __init__(self, name, used_by):
        self.name = name
        self.fn = name + ".ko"
        if used_by == '-':
            self.used_by = set()
        else:
            if used_by[-1] == ',':
                used_by = used_by[:-1]
            self.used_by = set(used_by.split(','))

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return "Module(name=%r,used_by=%r)" % (self.name,
                                               {I.name
                                                for I in self.used_by})

    def get_minfo(self):
        if self.minfo:
            return self.minfo

        try:
            st = os.stat(os.path.join(module_dir, self.fn))
        except FileNotFoundError:
            return None
        self.minfo = {"size": st[stat.ST_SIZE],
                      "mtime": st[stat.ST_MTIME]}
        return self.minfo

    def set_dirty(self):
        self.dirty = True
        for I in self.used_by:
            if not I.dirty:
                I.set_dirty()


def get_modules():
    """Return a dictionary of loaded modules and their dependencies."""
    res = {}
    with open("/proc/modules", "rt") as F:
        for ln in F:
            ln = ln.split(' ')
            m = Module(name=ln[0], used_by=ln[3])
            res[m.name] = m

    for I in res.values():
        I.used_by = {res[J] for J in I.used_by}

    return set(res.values())


def _topo_sort_modules(mod, done, res):
    if mod in done:
        return
    for I in mod.used_by:
        _topo_sort_modules(I, done, res)
    res.append(mod)
    done.add(mod)


def topo_sort_modules(mlist):
    """Return mlist topologically sorted"""
    done = set()
    res = []
    for I in mlist:
        _topo_sort_modules(I, done, res)
    return res


def set_dirty(mlist, fn_info):
    """Mark modules dirty that have changed on disk"""
    for I in mlist:
        if fn_info.get(I.fn, {}) != I.get_minfo():
            I.set_dirty()
            fn_info[I.fn] = I.minfo


# -------------------------------------------------------------------------


def args_modules_reload(parser):
    parser.add_argument(
        '--all', action="store_true", default=False, help="Reload all modules")


def cmd_modules_reload(args):
    """Remove and load all modules in the system. This is useful to load new code
    if the modules have been recompiled"""
    global module_dir
    module_dir = "/lib/modules/%s/modules" % (platform.uname()[2])
    try:
        mkt_module_data = os.path.join(module_dir, "mkt_module_data.pickle")
        with open(mkt_module_data, "rb") as F:
            fn_info = pickle.load(F)
    except FileNotFoundError:
        fn_info = {}

    modules = get_modules()
    if not args.all:
        set_dirty(modules, fn_info)
        modules = [I for I in modules if I.dirty]

    mods = topo_sort_modules(modules)
    if not mods:
        print("No modules changed. Use --all?")
        return

    print("Unloading %u modules" % (len(mods)))
    subprocess.check_call(["sudo", "modprobe", "-r"] + [I.name for I in mods])
    print("Loading %u modules" % (len(mods)))
    for I in mods:
        subprocess.check_call(["sudo", "modprobe", I.name])

    # Record the new timestamps for the now loaded modules
    subprocess.run(
        ["sudo", "bash", "-c",
         "exec cat > %s" % (mkt_module_data)],
        input=pickle.dumps(fn_info),
        check=True)
