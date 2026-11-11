from collections.abc import ItemsView, Mapping, MutableMapping
from typing import Any, TypeVar

_KT = TypeVar("_KT")
_VT_co = TypeVar("_VT_co", covariant=True)
_MM = TypeVar("_MM", bound=MutableMapping[Any, Any])

def url_join(base: str, *args: str) -> str: ...
def copy_kwargs[MM: MutableMapping[Any, Any]](dictionary: _MM) -> _MM: ...
def iterator[KT, VT_co](d: Mapping[_KT, _VT_co]) -> ItemsView[_KT, _VT_co]: ...
