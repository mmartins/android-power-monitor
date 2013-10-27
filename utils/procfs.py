#!/usr/bin/env python

__all__ = ['proc', 'ProcNode']

import os
from os.path import realpath
from sysfs import Node


class ProcNode(Node):
    def __init__(self, path='/proc'):
        self._path = realpath(path)
        if not self._path.startswith('/proc/') and not '/proc' == self._path:
            raise RuntimeError('Using this on non-procfs files is dangerous!')

        self.__dict__.update(dict.fromkeys(os.listdir(self._path)))

    def __repr__(self):
        return '<procfs.Node "{0}">'.format(self._path)


proc = ProcNode()
