from builtins import type as _type
from collections.abc import Callable, Iterable, Sequence
from typing import (
    Any,
    Protocol,
    Self,
    TypeVar,
    overload,
    type_check_only,
)

from markupsafe import Markup
from wtforms.form import BaseForm
from wtforms.meta import (
    DefaultMeta,
    _MultiDictLikeWithGetlist,
    _SupportsGettextAndNgettext,
)

_FormT = TypeVar("_FormT", bound=BaseForm)
_FieldT = TypeVar("_FieldT", bound=Field)
_FormT_contra = TypeVar("_FormT_contra", bound=BaseForm, contravariant=True)
_FieldT_contra = TypeVar("_FieldT_contra", bound=Field, contravariant=True)
type _Filter = Callable[[Any], Any]

@type_check_only
class _Validator(Protocol[_FormT_contra, _FieldT_contra]):
    def __call__(
        self,
        form: _FormT_contra,
        field: _FieldT_contra,
        /,
    ) -> object: ...

@type_check_only
class _Widget(Protocol[_FieldT_contra]):
    def __call__(self, field: _FieldT_contra, **kwargs: Any) -> Markup: ...

class Field:
    errors: Sequence[str]
    process_errors: Sequence[str]
    raw_data: list[Any] | None
    object_data: Any
    data: Any
    validators: Sequence[_Validator[Any, Self]]
    widget: _Widget[Self]
    do_not_call_in_templates: bool
    meta: DefaultMeta
    default: Any | None
    description: str
    render_kw: dict[str, Any]
    filters: Sequence[_Filter]
    flags: Flags
    name: str
    short_name: str
    id: str
    type: str
    label: Label
    def __new__(cls, *args: Any, **kwargs: Any) -> Self: ...
    def __init__(
        self,
        label: str | None = None,
        validators: tuple[_Validator[_FormT, Self], ...]
        | list[Any]
        | None = None,
        filters: Sequence[_Filter] = (),
        description: str = "",
        id: str | None = None,
        default: object | None = None,
        widget: _Widget[Self] | None = None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        _form: BaseForm | None = None,
        _prefix: str = "",
        _translations: _SupportsGettextAndNgettext | None = None,
        _meta: DefaultMeta | None = None,
    ) -> None: ...
    def __html__(self) -> str: ...
    def __call__(self, **kwargs: object) -> Markup: ...
    @classmethod
    def check_validators(
        cls,
        validators: Iterable[_Validator[_FormT, Self]] | None,
    ) -> None: ...
    def gettext(self, string: str) -> str: ...
    def ngettext(self, singular: str, plural: str, n: int) -> str: ...
    def validate(
        self,
        form: BaseForm,
        extra_validators: tuple[_Validator[_FormT, Self], ...]
        | list[Any] = (),
    ) -> bool: ...
    def pre_validate(self, form: BaseForm) -> None: ...
    def post_validate(
        self,
        form: BaseForm,
        validation_stopped: bool,
    ) -> None: ...
    def process(
        self,
        formdata: _MultiDictLikeWithGetlist | None,
        data: Any = ...,
        extra_filters: Sequence[_Filter] | None = None,
    ) -> None: ...
    def process_data(self, value: Any) -> None: ...
    def process_formdata(self, valuelist: list[Any]) -> None: ...
    def populate_obj(self, obj: object, name: str) -> None: ...
    @overload
    def __get__(
        self,
        obj: None,
        owner: _type[object] | None = None,
    ) -> UnboundField[Self]: ...
    @overload
    def __get__(
        self,
        obj: object,
        owner: _type[object] | None = None,
    ) -> Self: ...

class UnboundField[FieldT: Field]:
    creation_counter: int
    field_class: type[_FieldT]
    name: str | None
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    def __init__(
        self,
        field_class: type[_FieldT],
        *args: object,
        name: str | None = None,
        **kwargs: object,
    ) -> None: ...
    def bind(
        self,
        form: BaseForm,
        name: str,
        prefix: str = "",
        translations: _SupportsGettextAndNgettext | None = None,
        **kwargs: object,
    ) -> _FieldT: ...

class Flags:
    def __getattr__(self, name: str) -> Any | None: ...
    def __setattr__(self, name: str, value: object) -> None: ...
    def __delattr__(self, name: str) -> None: ...
    def __contains__(self, name: str) -> Any | None: ...

class Label:
    field_id: str
    text: str
    def __init__(self, field_id: str, text: str) -> None: ...
    def __html__(self) -> str: ...
    def __call__(self, text: str | None = None, **kwargs: Any) -> Markup: ...
