from collections.abc import MutableSequence, Sequence
from typing import Final, Literal, NoReturn, Self
from xml.dom.minidom import (
    Comment,
    Document,
    DOMImplementation,
    Element,
    ProcessingInstruction,
    Text,
)
from xml.sax import _SupportsReadClose
from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import (
    AttributesImpl,
    AttributesNSImpl,
    Locator,
    XMLReader,
)

from _typeshed import Incomplete

START_ELEMENT: Final = "START_ELEMENT"
END_ELEMENT: Final = "END_ELEMENT"
COMMENT: Final = "COMMENT"
START_DOCUMENT: Final = "START_DOCUMENT"
END_DOCUMENT: Final = "END_DOCUMENT"
PROCESSING_INSTRUCTION: Final = "PROCESSING_INSTRUCTION"
IGNORABLE_WHITESPACE: Final = "IGNORABLE_WHITESPACE"
CHARACTERS: Final = "CHARACTERS"
type _NSName = tuple[str | None, str]
type _DocumentFactory = DOMImplementation | None
type _Event = (
    tuple[Literal["START_ELEMENT"], Element]
    | tuple[Literal["END_ELEMENT"], Element]
    | tuple[Literal["COMMENT"], Comment]
    | tuple[Literal["START_DOCUMENT"], Document]
    | tuple[Literal["END_DOCUMENT"], Document]
    | tuple[Literal["PROCESSING_INSTRUCTION"], ProcessingInstruction]
    | tuple[Literal["IGNORABLE_WHITESPACE"], Text]
    | tuple[Literal["CHARACTERS"], Text]
)

class PullDOM(ContentHandler):
    document: Document | None
    documentFactory: _DocumentFactory
    firstEvent: list[Incomplete]
    lastEvent: list[Incomplete]
    elementStack: MutableSequence[Element | Document]
    pending_events: (
        list[
            Sequence[
                tuple[Literal["COMMENT"], str]
                | tuple[Literal["PROCESSING_INSTRUCTION"], str, str]
                | None
            ]
        ]
        | None
    )
    def __init__(self, documentFactory: _DocumentFactory = None) -> None: ...
    def pop(self) -> Element | Document: ...
    def setDocumentLocator(self, locator: Locator) -> None: ...
    def startPrefixMapping(self, prefix: str | None, uri: str) -> None: ...
    def endPrefixMapping(self, prefix: str | None) -> None: ...
    def startElementNS(
        self,
        name: _NSName,
        tagName: str | None,
        attrs: AttributesNSImpl,
    ) -> None: ...
    def endElementNS(self, name: _NSName, tagName: str | None) -> None: ...
    def startElement(self, name: str, attrs: AttributesImpl) -> None: ...
    def endElement(self, name: str) -> None: ...
    def comment(self, s: str) -> None: ...
    def processingInstruction(self, target: str, data: str) -> None: ...
    def ignorableWhitespace(self, chars: str) -> None: ...
    def characters(self, chars: str) -> None: ...
    def startDocument(self) -> None: ...
    def buildDocument(
        self,
        uri: str | None,
        tagname: str | None,
    ) -> Element: ...
    def endDocument(self) -> None: ...
    def clear(self) -> None: ...

class ErrorHandler:
    def warning(self, exception: BaseException) -> None: ...
    def error(self, exception: BaseException) -> NoReturn: ...
    def fatalError(self, exception: BaseException) -> NoReturn: ...

class DOMEventStream:
    stream: _SupportsReadClose[bytes] | _SupportsReadClose[str]
    parser: XMLReader
    bufsize: int
    pulldom: PullDOM
    def __init__(
        self,
        stream: _SupportsReadClose[bytes] | _SupportsReadClose[str],
        parser: XMLReader,
        bufsize: int,
    ) -> None: ...
    def __next__(self) -> _Event: ...
    def __iter__(self) -> Self: ...
    def getEvent(self) -> _Event | None: ...
    def expandNode(self, node: Document) -> None: ...
    def reset(self) -> None: ...
    def clear(self) -> None: ...

class SAX2DOM(PullDOM):
    def startElementNS(
        self,
        name: _NSName,
        tagName: str | None,
        attrs: AttributesNSImpl,
    ) -> None: ...
    def startElement(self, name: str, attrs: AttributesImpl) -> None: ...
    def processingInstruction(self, target: str, data: str) -> None: ...
    def ignorableWhitespace(self, chars: str) -> None: ...
    def characters(self, chars: str) -> None: ...

default_bufsize: Final[int]

def parse(
    stream_or_string: str
    | _SupportsReadClose[bytes]
    | _SupportsReadClose[str],
    parser: XMLReader | None = None,
    bufsize: int | None = None,
) -> DOMEventStream: ...
def parseString(
    string: str,
    parser: XMLReader | None = None,
) -> DOMEventStream: ...
