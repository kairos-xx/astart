import sys
from collections.abc import Callable
from typing import Final, Never, NewType, Self

if sys.version_info >= (3, 14):
    from _interpqueues import _UnboundOp
    class ItemInterpreterDestroyed(Exception): ...
    classonly = classmethod
    class UnboundItem:
        __slots__ = ()
        def __new__(cls) -> Never: ...
        @classonly
        def singleton(
            self,
            kind: str,
            module: str,
            name: str = "UNBOUND",
        ) -> Self: ...

    _UnboundErrorType = NewType("_UnboundErrorType", object)
    _UnboundRemoveType = NewType("_UnboundRemoveType", object)
    type _AnyUnbound = _UnboundErrorType | _UnboundRemoveType | UnboundItem
    UNBOUND_ERROR: Final[_UnboundErrorType]
    UNBOUND_REMOVE: Final[_UnboundRemoveType]
    UNBOUND: Final[UnboundItem]
    def serialize_unbound(unbound: _AnyUnbound) -> tuple[_UnboundOp]: ...
    def resolve_unbound(
        flag: _UnboundOp,
        exctype_destroyed: Callable[[str], BaseException],
    ) -> UnboundItem: ...
