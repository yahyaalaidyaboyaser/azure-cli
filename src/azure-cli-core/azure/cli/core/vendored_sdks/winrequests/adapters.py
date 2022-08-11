class HTTPAdapter:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def send(
            self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None
    ):
        return
    def build_response(self, request, response):
        return request.build_response(response)

    def retry(self, request, exception):
        return request.retry(exception)

    def is_exhausted(self):
        return False