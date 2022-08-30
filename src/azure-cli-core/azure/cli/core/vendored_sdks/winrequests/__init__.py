"""
Use windows-http to mock requests
https://github.com/psf/requests/blob/main/requests/__init__.py
"""
# windows-http will overwrite build-in http package if it is not imported
import http

from .api import delete, get, head, options, patch, post, put, request, Request, Session, Response

from .exceptions import *

from . import adapters


__version__ = '2.28.0'
