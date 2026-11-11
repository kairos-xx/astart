from re import Pattern
from typing import Final
from xml.etree.ElementTree import Element as Element
from xml.etree.ElementTree import QName as QName

from _typeshed import Incomplete

from ._functions_overloads import (
    SubElement as SubElement,
)
from ._functions_overloads import (
    _HasTag,
    _HasText,
)
from ._functions_overloads import (
    fromstring as fromstring,
)
from ._functions_overloads import (
    iterparse as iterparse,
)
from ._functions_overloads import (
    tostring as tostring,
)

xmlfile: Incomplete
NS_REGEX: Final[Pattern[str]]

def localname(node: _HasTag) -> str: ...
def whitespace(node: _HasText) -> None: ...
