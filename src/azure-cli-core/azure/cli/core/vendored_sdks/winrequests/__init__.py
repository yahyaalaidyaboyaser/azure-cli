"""
Use windows-http to mock requests
https://github.com/psf/requests/blob/main/requests/__init__.py
"""
from .api import delete, get, head, options, patch, post, put, request, Request, Session, Response

from .exceptions import *

from . import adapters


__version__ = '2.28.0'
