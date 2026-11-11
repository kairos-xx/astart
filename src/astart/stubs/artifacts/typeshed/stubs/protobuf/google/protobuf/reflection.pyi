from typing import Any, Self

from google._upb._message import MessageMeta

MESSAGE_CLASS_CACHE: dict[str, Any]

class GeneratedProtocolMessageType(MessageMeta):
    def __new__(
        cls,
        name: str,
        bases: tuple[type, ...],
        dictionary: dict[str, Any],
    ) -> Self: ...
