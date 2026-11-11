from typing import Any, Protocol

class DOMImplementation(Protocol):
    def hasFeature(self, feature: str, version: str | None, /) -> bool: ...
    def createDocument(
        self,
        namespaceUri: str,
        qualifiedName: str,
        doctype: Any | None,
        /,
    ) -> Any: ...
    def createDocumentType(
        self,
        qualifiedName: str,
        publicId: str,
        systemId: str,
        /,
    ) -> Any: ...
