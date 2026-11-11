from collections.abc import Iterable
from threading import Thread
from typing import Literal, Self

from _typeshed import Incomplete
from _typeshed.wsgi import StartResponse, WSGIApplication, WSGIEnvironment
from waitress.server import TcpWSGIServer

type _WSGIServerParams = Incomplete

def get_free_port() -> tuple[str, int]: ...
def check_server(
    host: str,
    port: int,
    path_info: str = "/",
    timeout: float = 3,
    retries: int = 30,
) -> int: ...

class StopableWSGIServer(TcpWSGIServer):
    was_shutdown: bool
    runner: Thread
    test_app: WSGIApplication
    application_url: str
    def wrapper(
        self,
        environ: WSGIEnvironment,
        start_response: StartResponse,
    ) -> Iterable[bytes]: ...
    def run(self) -> None: ...
    def shutdown(self, debug: bool = False) -> Literal[True]: ...
    @classmethod
    def create(
        cls,
        application: WSGIApplication,
        **kwargs: _WSGIServerParams,
    ) -> Self: ...
    def wait(self, retries: int = 30) -> bool: ...
