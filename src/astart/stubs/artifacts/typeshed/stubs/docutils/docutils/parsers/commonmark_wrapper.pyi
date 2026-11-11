from typing import Literal

from docutils import parsers

type _ParserName = Literal["pycmark", "myst", "recommonmark"]
commonmark_parser_names: tuple[_ParserName, ...]
Parser: type[parsers.Parser]
parser_name: _ParserName
