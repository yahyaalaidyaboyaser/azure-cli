import datetime
import os
import windows.http as HTTP

from collections import OrderedDict

from .utils import to_key_val_list, get_environ_proxies
from .compat import Mapping

from .dummy import Dummy


class Raw:
    # BlobClient's default transport(RequestsTransport) calls response.raw.enforce_content_length = True,
    # I don't want to patch its source code, so I'm using this class to wrap response.raw
    def __init__(self, raw):
        self._raw = raw
        self.enforce_content_length = False

    def __getattr__(self, name):
        return getattr(self._raw, name)


class Response:
    def __init__(self, response):
        self._response = response
        # telemetry calls this method.
        self.elapsed = datetime.timedelta(seconds=1)
        self.raw = Raw(response.raw)

    @property
    def headers(self):
        return dict(self._response.headers) if self._response.headers else {}

    def __getattr__(self, name):
        return getattr(self._response, name)

    # def __setattr__(self, key, value):
    #     self._response.__setattr__(key, value)


class Session(HTTP.Session):
    def __init__(self, *args, **kwargs):
        self.proxies = kwargs.pop('proxies', None)
        self.cert = []
        # self.allow_redirects = False
        self.resolve_redirects = []
        self.adapters = Dummy()
        self.auth = None
        super().__init__(*args, **kwargs)

    def request(self, *args, **kwargs):
        return Response(super().request(*args, **kwargs))

    def request_sync(self, *args, **kwargs):
        return Response(super().request_sync(*args, **kwargs))

    def get(self, *args, **kwargs):
        return Response(super().get(*args, **kwargs))

    def head(self, *args, **kwargs):
        return Response(super().head(*args, **kwargs))

    def post(self, *args, **kwargs):
        return Response(super().post(*args, **kwargs))

    def put(self, *args, **kwargs):
        return Response(super().put(*args, **kwargs))

    def patch(self, *args, **kwargs):
        return Response(super().patch(*args, **kwargs))

    def delete(self, *args, **kwargs):
        return Response(super().delete(*args, **kwargs))

    def send(self, request, **kwargs):
        # msrest.service_client ServiceClient call this method.
        for k, v in kwargs.items():
            try:
                setattr(request, k, v)
            except:
                pass
        # Not working, if auth is assigned to KeyVaultAuthBase install, [WinError 4317] The operation identifier is not
        # valid is raised. `auth` should be either a callable, a (username, password) tuple, or a “username” string.
        # request.auth = self.auth
        return Response(super().send(request))

    def mount(self, *args, **kwargs):
        # msal.application ClientApplication
        pass

    def prepare_request(self, request):
        # azure-cli-core call this method.
        return request.prepare()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        """
        azure-cli-core send_raw_request() call this method.

        Check the environment and merge it with some settings.
        :rtype: dict
        """
        # Gather clues from the surrounding environment.
        if True:
            # Set environment's proxies.
            no_proxy = proxies.get("no_proxy") if proxies is not None else None
            env_proxies = get_environ_proxies(url, no_proxy=no_proxy)
            for (k, v) in env_proxies.items():
                proxies.setdefault(k, v)

            # Look for requests environment configuration
            # and be compatible with cURL.
            if verify is True or verify is None:
                verify = (
                        os.environ.get("REQUESTS_CA_BUNDLE")
                        or os.environ.get("CURL_CA_BUNDLE")
                        or verify
                )

        # Merge all the kwargs.
        proxies = merge_setting(proxies, self.proxies)
        stream = merge_setting(stream, self.stream)
        verify = merge_setting(verify, self.verify)
        cert = merge_setting(cert, self.cert)

        return {"proxies": proxies, "stream": stream, "verify": verify, "cert": cert}


def merge_setting(request_setting, session_setting, dict_class=OrderedDict):
    """Determines appropriate setting for a given request, taking into account
    the explicit setting on that request, and the setting in the session. If a
    setting is a dictionary, they will be merged together using `dict_class`
    """

    if session_setting is None:
        return request_setting

    if request_setting is None:
        return session_setting

    # Bypass if not a dictionary (e.g. verify)
    if not (
            isinstance(session_setting, Mapping) and isinstance(request_setting, Mapping)
    ):
        return request_setting

    merged_setting = dict_class(to_key_val_list(session_setting))
    merged_setting.update(to_key_val_list(request_setting))

    # Remove keys that are set to None. Extract keys first to avoid altering
    # the dictionary during iteration.
    none_keys = [k for (k, v) in merged_setting.items() if v is None]
    for key in none_keys:
        del merged_setting[key]

    return merged_setting


def _pass(func):
    assert func in {'delete', 'get', 'head', 'options', 'patch', 'post', 'put', 'request'}

    def wrapper(*args, **kwargs):
        with HTTP.Session() as session:
            r = getattr(session, func, )(*args, **kwargs)

        return Response(r)

    return wrapper


for i in ['delete', 'get', 'head', 'options', 'patch', 'post', 'put', 'request']:
    globals()[i] = _pass(i)

Request = HTTP.Request
PreparedRequest = HTTP.PreparedRequest
