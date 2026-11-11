from collections.abc import Callable
from typing import Any

from ..pytree import _RawNode
from .grammar import Grammar

type _Convert = Callable[[Grammar, _RawNode], Any]
