"""A generic persistence layer, optionally encrypted on Windows, OSX, and Linux.

Should a certain encryption is unavailable, exception will be raised at run-time,
rather than at import time.

By successfully creating and using a certain persistence object,
app developer would naturally know whether the data are protected by encryption.
"""
import abc
import os
import errno
import hashlib
import logging
import sys
import time

from pathlib import Path  # Built-in in Python 3



try:
    ABC = abc.ABC
except AttributeError:  # Python 2.7, abc exists, but not ABC
    ABC = abc.ABCMeta("ABC", (object,), {"__slots__": ()})  # type: ignore


logger = logging.getLogger(__name__)


def _mkdir_p(path):
    """Creates a directory, and any necessary parents.

    If the path provided is an existing file, this function raises an exception.
    :param path: The directory name that should be created.
    """
    if not path:
        return  # NO-OP

    if sys.version_info >= (3, 2):
        os.makedirs(path, exist_ok=True)
        return

    # This fallback implementation is based on a Stack Overflow question:
    # https://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    # Known issue: it won't work when the path is a root folder like "C:\\"
    try:
        os.makedirs(path)
    except OSError as exp:
        if exp.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def _auto_hash(input_string):
    return hashlib.sha256(input_string.encode('utf-8')).hexdigest()

# We do not aim to wrap every os-specific exception.
# Here we standardize only the most common ones,
# otherwise caller would need to catch os-specific underlying exceptions.
class PersistenceError(IOError):  # Use IOError rather than OSError as base,
    """The base exception for persistence."""
        # because historically an IOError was bubbled up and expected.
        # https://github.com/AzureAD/microsoft-authentication-extensions-for-python/blob/0.2.2/msal_extensions/token_cache.py#L38
        # Now we want to maintain backward compatibility even when using Python 2.x
        # It makes no difference in Python 3.3+ where IOError is an alias of OSError.
    def __init__(self, err_no=None, message=None, location=None):  # pylint: disable=useless-super-delegation
        super(PersistenceError, self).__init__(err_no, message, location)


class PersistenceNotFound(PersistenceError):
    """This happens when attempting BasePersistence.load() on a non-existent persistence instance"""
    def __init__(self, err_no=None, message=None, location=None):
        super(PersistenceNotFound, self).__init__(
            err_no=errno.ENOENT,
            message=message or "Persistence not found",
            location=location)

class PersistenceEncryptionError(PersistenceError):
    """This could be raised by persistence.save()"""

class PersistenceDecryptionError(PersistenceError):
    """This could be raised by persistence.load()"""


def build_encrypted_persistence(location):
    """Build a suitable encrypted persistence instance based your current OS.

    If you do not need encryption, then simply use ``FilePersistence`` constructor.
    """
    # Does not (yet?) support fallback_to_plaintext flag,
    # because the persistence on Windows and macOS do not support built-in trial_run().
    if sys.platform.startswith('win'):
        return FilePersistenceWithDataProtection(location)


class BasePersistence(ABC):
    """An abstract persistence defining the common interface of this family"""

    is_encrypted = False  # Default to False. To be overridden by sub-classes.

    @abc.abstractmethod
    def save(self, content):
        # type: (str) -> None
        """Save the content into this persistence"""
        raise NotImplementedError

    @abc.abstractmethod
    def load(self):
        # type: () -> str
        """Load content from this persistence.

        Could raise PersistenceNotFound if no save() was called before.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def time_last_modified(self):
        """Get the last time when this persistence has been modified.

        Could raise PersistenceNotFound if no save() was called before.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_location(self):
        """Return the file path which this persistence stores (meta)data into"""
        raise NotImplementedError


def _open(location):
    return os.open(location, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
        # The 600 seems no-op on NTFS/Windows, and that is fine


class FilePersistence(BasePersistence):
    """A generic persistence, storing data in a plain-text file"""

    def __init__(self, location):
        if not location:
            raise ValueError("Requires a file path")
        self._location = os.path.expanduser(location)
        _mkdir_p(os.path.dirname(self._location))

    def save(self, content):
        # type: (str) -> None
        """Save the content into this persistence"""
        with os.fdopen(_open(self._location), 'w+') as handle:
            handle.write(content)

    def load(self):
        # type: () -> str
        """Load content from this persistence"""
        try:
            with open(self._location, 'r') as handle:  # pylint: disable=unspecified-encoding
                return handle.read()
        except EnvironmentError as exp:  # EnvironmentError in Py 2.7 works across platform
            if exp.errno == errno.ENOENT:
                raise PersistenceNotFound(
                    message=(
                        "Persistence not initialized. "
                        "You can recover by calling a save() first."),
                    location=self._location,
                )
            raise


    def time_last_modified(self):
        try:
            return os.path.getmtime(self._location)
        except EnvironmentError as exp:  # EnvironmentError in Py 2.7 works across platform
            if exp.errno == errno.ENOENT:
                raise PersistenceNotFound(
                    message=(
                        "Persistence not initialized. "
                        "You can recover by calling a save() first."),
                    location=self._location,
                )
            raise

    def touch(self):
        """To touch this file-based persistence without writing content into it"""
        Path(self._location).touch()  # For os.path.getmtime() to work

    def get_location(self):
        return self._location


LibsecretPersistence = FilePersistence
FilePersistenceWithDataProtection = FilePersistence
KeychainPersistence = FilePersistence
