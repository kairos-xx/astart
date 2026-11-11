from collections.abc import Callable
from typing import Any, ClassVar

from channels.routing import ProtocolTypeRouter
from channels.utils import _ChannelApplication
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.test.testcases import TransactionTestCase

type DaphneProcess = Any
type _StaticWrapper = Callable[[ProtocolTypeRouter], _ChannelApplication]

def make_application(*, static_wrapper: _StaticWrapper | None) -> Any: ...
def set_database_connection() -> None: ...

class ChannelsLiveServerTestCase(TransactionTestCase):
    host: ClassVar[str] = "localhost"
    ProtocolServerProcess: ClassVar[type[DaphneProcess]] = ...
    static_wrapper: ClassVar[type[ASGIStaticFilesHandler]] = ...
    serve_static: ClassVar[bool] = True
    @property
    def live_server_url(self) -> str: ...
    @property
    def live_server_ws_url(self) -> str: ...
