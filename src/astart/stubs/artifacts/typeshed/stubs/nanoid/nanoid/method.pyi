from collections.abc import Callable, Sequence

type _Algorithm = Callable[[int], Sequence[int]]

def method(algorithm: _Algorithm, alphabet: str, size: int) -> str: ...
