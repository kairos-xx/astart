from importlib.resources._common import Package as Package

__all__ = [
    "Package",
    "ResourceReader",
    "as_file",
    "contents",
    "files",
    "is_resource",
    "open_binary",
    "open_text",
    "path",
    "read_binary",
    "read_text",
]

from importlib.resources._common import Anchor as Anchor

__all__ += ["Anchor"]
from importlib.resources._common import as_file as as_file
from importlib.resources._common import files as files
from importlib.resources._functional import (
    contents as contents,
)
from importlib.resources._functional import (
    is_resource as is_resource,
)
from importlib.resources._functional import (
    open_binary as open_binary,
)
from importlib.resources._functional import (
    open_text as open_text,
)
from importlib.resources._functional import (
    path as path,
)
from importlib.resources._functional import (
    read_binary as read_binary,
)
from importlib.resources._functional import (
    read_text as read_text,
)
from importlib.resources.abc import ResourceReader as ResourceReader
