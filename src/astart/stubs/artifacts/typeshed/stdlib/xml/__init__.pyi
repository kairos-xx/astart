import sys

__all__ = ["dom", "etree", "parsers", "sax"]  # noqa: F822  # pyright: ignore[reportUnsupportedDunderAll]
if sys.version_info >= (3, 15):
    __all__ += ["is_valid_name"]  # pyright: ignore[reportUnsupportedDunderAll]
    from xml.utils import is_valid_name as is_valid_name
    from xml.utils import is_valid_text as is_valid_text
