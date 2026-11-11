from pathlib import Path
from typing import Any, Final, Required, TypedDict, TypeVar, type_check_only

from _typeshed import StrPath
from docutils import Component, nodes
from docutils.frontend import Values
from docutils.io import Output
from docutils.languages import LanguageImporter

_S = TypeVar("_S")
__docformat__: Final = "reStructuredText"

@type_check_only
class _WriterParts(TypedDict, total=False):
    whole: Required[str | bytes]
    encoding: Required[str]
    errors: Required[str]
    version: Required[str]
    body: str
    body_prefix: str
    body_pre_docinfo: str
    body_suffix: str
    docinfo: str
    footer: str
    fragment: str
    head: str
    head_prefix: str
    header: str
    html_body: str
    html_head: str
    html_prolog: str
    html_subtitle: str
    html_title: str
    meta: str
    stylesheet: str
    subtitle: str
    title: str
    pepnum: str
    abstract: str
    dedication: str
    fallbacks: str
    latex_preamble: str
    pdfsetup: str
    requirements: str
    titledata: str

class Writer[S](Component):
    parts: _WriterParts
    language: LanguageImporter | None = None
    document: nodes.document | None = None
    destination: Output | None = None
    output: _S | None = None
    def __init__(self) -> None: ...
    def write(
        self,
        document: nodes.document,
        destination: Output,
    ) -> str | bytes | None: ...
    def translate(self) -> None: ...
    def assemble_parts(self) -> None: ...

class UnfilteredWriter(Writer[_S]): ...

class DoctreeTranslator(nodes.NodeVisitor):
    settings: Values
    def __init__(self, document: nodes.document) -> None: ...
    def uri2path(
        self,
        uri: str,
        output_path: StrPath | None = None,
    ) -> Path: ...

WRITER_ALIASES: Final[dict[str, str]]

def get_writer_class(writer_name: str) -> type[Writer[Any]]: ...
