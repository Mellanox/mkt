"""Directory logic
"""
import os

class DirList(object):
    def __init__(self):
        self.list = set()

    def add(self, dfn):
        """Maintain a list of directories such that there are no subdirectories of
        other elements in the list."""
        if isinstance(dfn, bytes):
            dfn = dfn.decode()
        while dfn[-1] == '/':
            dfn = dfn[:-1]

        dfn = os.path.realpath(dfn)

        torm = set()
        for I in self.list:
            if dfn.startswith(I):
                return
            if I.startswith(dfn):
                torm.add(I)
        self.list.difference_update(torm)
        self.list.add(dfn)

    def as_docker_bind(self):
        res = []
        for I in sorted(self.list):
            res.append("-v")
            res.append("%s:%s:Z" % (I, I))
        return res
