from collections.abc import Callable

import numpy as np

__all__ = ["clear_cache", "get_filter", "sinc_window"]
FILTER_CACHE: dict[
    str,
    tuple[np.ndarray[tuple[int], np.dtype[np.float64]], int, float],
]
FILTER_FUNCTIONS: list[str]
type _FilterType = (
    str | Callable[[int], np.ndarray[tuple[int], np.dtype[np.float64]]]
)

def sinc_window(
    num_zeros: int = 64,
    precision: int = 9,
    window: Callable[[int], np.ndarray[tuple[int], np.dtype[np.float64]]]
    | None = None,
    rolloff: float = 0.945,
) -> tuple[np.ndarray[tuple[int], np.dtype[np.float64]], int, float]: ...
def get_filter(
    name_or_function: _FilterType,
    *,
    num_zeros: int = 64,
    precision: int = 9,
    rolloff: float = 0.945,
) -> tuple[np.ndarray[tuple[int], np.dtype[np.float64]], int, float]: ...
def load_filter(
    filter_name: str,
) -> tuple[np.ndarray[tuple[int], np.dtype[np.float64]], int, float]: ...
def clear_cache() -> None: ...
