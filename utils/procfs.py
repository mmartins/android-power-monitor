#!/usr/bin/env python

__all__ = ['proc', 'ProcNode']

import os
from os.path import isdir, isfile, join, realpath
from sysfs import Node

class ProcNode(Node):

    def __init__(self, path='/proc'):
        self._path_ = realpath(path)
        if not self._path_.startswith('/proc/') and not '/proc' == self._path_:
            raise RuntimeError('Using this on non-procfs files is dangerous!')

        self.__dict__.update(dict.fromkeys(os.listdir(self._path_)))

    def __repr__(self):
        return '<procfs.Node "{0}">'.format(self._path_)

proc = ProcNode()
