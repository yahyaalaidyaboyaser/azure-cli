"""Provides a mechanism for not competing with other processes interacting with an MSAL cache."""
import os
import sys
import errno
import time
import logging
from distutils.version import LooseVersion


logger = logging.getLogger(__name__)

class Dummy:
    def dummy(self, *args, **kw):
        pass

    def __getattr__(self, name):
        return self.dummy

class CrossPlatLock(object):
    """Offers a mechanism for waiting until another process is finished interacting with a shared
    resource. This is specifically written to interact with a class of the same name in the .NET
    extensions library.
    """
    def __init__(self, lockfile_path):
        pass

    def _try_to_create_lock_file(self):
        return True

    def __enter__(self):
        return Dummy()

    def __exit__(self, *args):
        pass
