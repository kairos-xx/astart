import logging
from collections.abc import Callable
from typing import Any, TypeVar

import click

type _AnyCallable = Callable[..., Any]
_FC = TypeVar("_FC", bound=_AnyCallable | click.Command)

def simple_verbosity_option(
    logger: logging.Logger | str | None = None,
    *names: str,
    **kwargs: Any,
) -> Callable[[_FC], _FC]: ...
