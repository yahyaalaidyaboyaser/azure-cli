"""
HttpTransport implementation for windows-http

Modified from https://github.com/Azure/azure-sdk-for-python-pr/blob/win-transport/sdk/keyvault/azure-keyvault-secrets/tests/transport/windows_os_transport.py  # pylint: disable=line-too-long
"""
from azure.core.pipeline.transport import HttpResponse, HttpTransport, HttpRequest
from windows.http import Response, Session
from typing import ContextManager, Iterator, Optional

from azure.core import PipelineClient


class WindowsHttpTransportResponse(HttpResponse):
    def __init__(self, request: HttpRequest, windows_http_response: Response,
                 stream_contextmanager: Optional[ContextManager] = None):
        super().__init__(request, windows_http_response)
        self.status_code = windows_http_response.status_code
        self.headers = windows_http_response.headers
        self.reason = windows_http_response.reason
        self.content_type = windows_http_response.headers.get('content-type')
        self.stream_contextmanager = stream_contextmanager

    def body(self):
        return self.internal_response.content

    def stream_download(self, _, **kwargs) -> Iterator[bytes]:
        return WindowsHttpStreamDownloadGenerator(_, self)


class WindowsHttpStreamDownloadGenerator:
    def __init__(self, _, response):
        self.response = response
        self.iter_func = response.internal_response.iter_content()

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self.iter_func)
        except StopIteration:
            self.response.stream_contextmanager.close()
            raise


class WindowsHttpTransport(HttpTransport):
    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        self.client = None

    def open(self):
        self.client = Session()

    def close(self):
        self.client = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def send(self, request: HttpRequest, **kwargs) -> HttpResponse:
        if self.client is None:
            self.client = Session()

        stream_response = kwargs.pop("stream", False)

        parameters = {
            "method": request.method,
            "url": request.url,
            "headers": request.headers.items(),
            "data": request.data,
            "files": request.files,
            **kwargs
        }

        if type(parameters["data"]) is str:
            parameters["data"] = parameters["data"].encode('utf-8')

        stream_ctx = None

        if stream_response:
            stream_ctx = self.client.request(**parameters, stream=True)
            response = stream_ctx.__enter__()

        else:
            response = self.client.request(**parameters)
        return WindowsHttpTransportResponse(request, response, stream_contextmanager=stream_ctx)


class WindowsPipelineClient(PipelineClient):
    def __init__(self, base_url, **kwargs):
        kwargs['transport'] = WindowsHttpTransport()
        super().__init__(base_url, **kwargs)
