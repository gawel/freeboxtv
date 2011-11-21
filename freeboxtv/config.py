# -*- coding: utf-8 -*-
from ConfigObject import ConfigObject
import sys
import os

filename = os.path.expanduser(os.path.join('~/.freeboxtv', 'config.ini'))
dirname = os.path.dirname(filename)
if not os.path.isdir(dirname):
    os.makedirs(dirname)

config = ConfigObject(filename=filename)
config.__name__ = __name__
config.__file__ = __file__
config.__path__ = __file__
sys.modules[__name__] = config


