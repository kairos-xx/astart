from html import escape as escape
from io import FileIO, TextIOWrapper
from queue import Empty as Empty
from queue import Queue as Queue
from typing import IO

class cgi_FieldStorage:
    filename: str
    file: IO[bytes]
    def make_file(self) -> TextIOWrapper | FileIO: ...

def parse_header(line: str) -> tuple[str, dict[str, str]]: ...
