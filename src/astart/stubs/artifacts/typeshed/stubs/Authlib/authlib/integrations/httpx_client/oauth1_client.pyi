from collections.abc import Generator
from typing import NoReturn

from _typeshed import Incomplete
from authlib.oauth1 import ClientAuth
from authlib.oauth1.client import OAuth1Client as _OAuth1Client

type _Response = Incomplete
type _Request = Incomplete

class OAuth1Auth(ClientAuth):
    requires_request_body: bool
    def auth_flow(
        self,
        request: _Request,
    ) -> Generator[_Request, _Response]: ...

class AsyncOAuth1Client(_OAuth1Client):
    auth_class = OAuth1Auth
    def __init__(
        self,
        client_id,
        client_secret=None,
        token=None,
        token_secret=None,
        redirect_uri=None,
        rsa_key=None,
        verifier=None,
        signature_method=...,
        signature_type=...,
        force_include_body=False,
        **kwargs,
    ) -> None: ...
    async def fetch_access_token(self, url, verifier=None, **kwargs): ...
    @staticmethod
    def handle_error(
        error_type: str | None,
        error_description: str | None,
    ) -> NoReturn: ...

class OAuth1Client(_OAuth1Client):
    auth_class = OAuth1Auth
    def __init__(
        self,
        client_id,
        client_secret=None,
        token=None,
        token_secret=None,
        redirect_uri=None,
        rsa_key=None,
        verifier=None,
        signature_method=...,
        signature_type=...,
        force_include_body=False,
        **kwargs,
    ) -> None: ...
    @staticmethod
    def handle_error(
        error_type: str | None,
        error_description: str | None,
    ) -> NoReturn: ...
