from collections.abc import Iterator

class ChevronError(SyntaxError): ...

def grab_literal(template: str, l_del: str | None) -> tuple[str, str]: ...
def l_sa_check(
    template: str,
    literal: str,
    is_standalone: bool,
) -> bool | None: ...
def r_sa_check(template: str, tag_type: str, is_standalone: bool) -> bool: ...
def parse_tag(
    template: str,
    l_del: str | None,
    r_del: str | None,
) -> tuple[tuple[str, str], str]: ...
def tokenize(
    template: str,
    def_ldel: str | None = "{{",
    def_rdel: str | None = "}}",
) -> Iterator[tuple[str, str]]: ...
