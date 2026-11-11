from collections.abc import MutableMapping
from typing import Protocol, type_check_only

from bleach import _HTMLAttrKey

type _HTMLAttrs = MutableMapping[_HTMLAttrKey, str]

@type_check_only
class _Callback(Protocol):
    def __call__(
        self,
        attrs: _HTMLAttrs,
        new: bool = ...,
        /,
    ) -> _HTMLAttrs: ...

def nofollow(attrs: _HTMLAttrs, new: bool = False) -> _HTMLAttrs: ...
def target_blank(attrs: _HTMLAttrs, new: bool = False) -> _HTMLAttrs: ...
