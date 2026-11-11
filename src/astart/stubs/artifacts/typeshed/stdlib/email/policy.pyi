from collections.abc import Callable
from email._policybase import Compat32 as Compat32
from email._policybase import Policy as Policy
from email._policybase import _MessageFactory, _MessageT
from email._policybase import compat32 as compat32
from email.contentmanager import ContentManager
from email.message import EmailMessage
from typing import Any, Self, overload

__all__ = [
    "HTTP",
    "SMTP",
    "Compat32",
    "EmailPolicy",
    "Policy",
    "compat32",
    "default",
    "strict",
]

class EmailPolicy(Policy[_MessageT]):
    utf8: bool
    refold_source: str
    header_factory: Callable[[str, Any], Any]
    content_manager: ContentManager
    @overload
    def __init__(
        self: EmailPolicy[EmailMessage],
        *,
        max_line_length: int | None = ...,
        linesep: str = ...,
        cte_type: str = ...,
        raise_on_defect: bool = ...,
        mangle_from_: bool = ...,
        message_factory: None = None,
        verify_generated_headers: bool = ...,
        utf8: bool = ...,
        refold_source: str = ...,
        header_factory: Callable[[str, str], str] = ...,
        content_manager: ContentManager = ...,
    ) -> None: ...
    @overload
    def __init__(
        self,
        *,
        max_line_length: int | None = ...,
        linesep: str = ...,
        cte_type: str = ...,
        raise_on_defect: bool = ...,
        mangle_from_: bool = ...,
        message_factory: _MessageFactory[_MessageT] | None = ...,
        verify_generated_headers: bool = ...,
        utf8: bool = ...,
        refold_source: str = ...,
        header_factory: Callable[[str, str], str] = ...,
        content_manager: ContentManager = ...,
    ) -> None: ...
    def header_source_parse(
        self,
        sourcelines: list[str],
    ) -> tuple[str, str]: ...
    def header_store_parse(self, name: str, value: Any) -> tuple[str, Any]: ...
    def header_fetch_parse(self, name: str, value: str) -> Any: ...
    def fold(self, name: str, value: str) -> Any: ...
    def fold_binary(self, name: str, value: str) -> bytes: ...
    def clone(
        self,
        *,
        max_line_length: int | None = ...,
        linesep: str = ...,
        cte_type: str = ...,
        raise_on_defect: bool = ...,
        mangle_from_: bool = ...,
        message_factory: _MessageFactory[_MessageT] | None = ...,
        verify_generated_headers: bool = ...,
        utf8: bool = ...,
        refold_source: str = ...,
        header_factory: Callable[[str, str], str] = ...,
        content_manager: ContentManager = ...,
    ) -> Self: ...

default: EmailPolicy[EmailMessage]
SMTP: EmailPolicy[EmailMessage]
SMTPUTF8: EmailPolicy[EmailMessage]
HTTP: EmailPolicy[EmailMessage]
strict: EmailPolicy[EmailMessage]
