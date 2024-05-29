from js import Response as JSResponse
from js import Headers as JSHeaders
from js import URL as JSURL

import json
from inspect import signature, Parameter
from urllib.parse import urlparse, parse_qs
from typing import get_type_hints
import re

status_details = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}

class Request:
    def __init__(self, scope, url):
        self.scope = scope
        self.headers = scope["headers"]        
        self.url = urlparse(url)
        self.params = parse_qs(self.url.query)
        self.path = self.url.path
        self.scope["path"] = self.path

class Response:
    def __init__(self, body, headers = {}, status = 200):
        self.headers = headers
        self.body = body
        self.status = status

class JSONResponse(Response):
    def __init__(self, body, headers = {}, status = 200):
        self.headers = headers
        self.body = json.dumps(body)
        self.status = status
        self.headers["content-type"] = "application/json"

class HTMLResponse(Response):
    def __init__(self, body, headers = {}, status = 200):
        super().__init__(body, headers, status)
        self.headers["content-type"] = "text/html; charset=utf-8"

class HTTPException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        if detail is None:
            detail = status_details[status_code]
        self.status_code = status_code
        self.detail = detail
        self.headers = headers

    def __str__(self) -> str:
        return f"{self.status_code}: {self.detail}"

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"

class Server:
    async def serve(app, request, env):
        scope = {
            'type': 'http',
            'method': request.method,
            'headers': request.headers.as_object_map(),
            'env': env
        }
        try:
            resp = await app(Request(scope, request.url))
            headers = JSHeaders.new(resp.headers.items())
            body = resp.body
            status = resp.status

        except HTTPException as e:
            headers = JSHeaders.new(e.headers.items())
            body = e.detail
            status = e.status_code
            
        return JSResponse.new(body, headers=headers, status=status)

# App

class App:
    def __init__(self):
        self.routes = []

    def add_route(self, path, handler, method = "get"):
        compiled, params = self.path_regex(path)
        self.routes.append((compiled, params, method.lower(), handler))

    def route(self, path):
        def decorator(handler, method):
            self.add_route(path, handler, method)
            return handler
        return decorator  

    def get(self, path):
        def decorator(handler):
            self.add_route(path, handler, "get")
            return handler
        return decorator  

    def post(self, path):
        def decorator(handler):
            self.add_route(path, handler, "post")
            return handler
        return decorator  

    def put(self, path):
        def decorator(handler):
            self.add_route(path, handler, "put")
            return handler
        return decorator  

    def head(self, path):
        def decorator(handler):
            self.add_route(path, handler, "head")
            return handler
        return decorator

    async def __call__(self, request):
        path = request.path
        handler, path_params = self.find_route(path, request.method.lower())
        params = await self.get_params(request, handler, path_params)
        return await handler(**params)
        
    def path_regex(self, path):
        params = []
        pattern = re.sub(r'\{([^/]+)\}', r'(?:P<\1>[^/]+)', path)
        pattern = '^' + pattern + '$'
        compiled = re.compile(pattern)
        params = re.findall(r'\{([^/]+)\}', path)
        
        return compiled, params

    def find_route(self, path, req_method):
        for compiled, params, method, handler in self.routes:
            if req_method != method:
                continue
            match = compiled.match(path)
            if match:
                path_params = match.groupdict()
                return handler, path_params
        return self.default_response, {}

    def default_response(self, request, **params):
        return Response(status=404, body="Not Found")

    async def get_params(self, request, handler, path_params):
        params = request.params
        sig = signature(handler)
        converted_params = {}
        type_hints = get_type_hints(handler)

        for name, param in sig.parameters.items():
            if name in path_params:
                value = path_params[name]

                if param.annotation != param.empty:
                    value = param.annotation(value)
                
                converted_params[name] = value

            elif name in type_hints and type_hints[name] == Request:
                converted_params[name] = request

            elif name in params:
                value = params[name][0]
                if param.annotation != param.empty:
                    value = param.annotation(value)

                converted_params[name] = value

            else:
                if param.default != param.empty:
                    converted_params[name] = param.default

        return converted_params

# BaseModel

class BaseModel:
    def __init__(self):
        pass