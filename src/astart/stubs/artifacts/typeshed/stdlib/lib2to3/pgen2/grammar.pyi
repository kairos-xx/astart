from typing import Self

from _typeshed import StrPath

type _Label = tuple[int, str | None]
type _DFA = list[list[tuple[int, int]]]
type _DFAS = tuple[_DFA, dict[int, int]]

class Grammar:
    symbol2number: dict[str, int]
    number2symbol: dict[int, str]
    states: list[_DFA]
    dfas: dict[int, _DFAS]
    labels: list[_Label]
    keywords: dict[str, int]
    tokens: dict[int, int]
    symbol2label: dict[str, int]
    start: int
    def dump(self, filename: StrPath) -> None: ...
    def load(self, filename: StrPath) -> None: ...
    def copy(self) -> Self: ...
    def report(self) -> None: ...

opmap_raw: str
opmap: dict[str, str]
