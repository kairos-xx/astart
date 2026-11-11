from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, NamedTuple

from _typeshed import Unused
from django import forms
from django.db.models import Choices
from django.forms import Widget
from django_stubs_ext import StrOrPromise

DJANGO_50: bool
type _ClassLevelWidget = Any
type _ValidatorCallable = Callable[[Any], None]
type _Choice = tuple[Any, Any]
type _ChoiceNamedGroup = tuple[str, Iterable[_Choice]]
type _Choices = Iterable[_Choice | _ChoiceNamedGroup]
type _ChoicesMapping = Mapping[Any, Any]
type _ChoicesInput = (
    _Choices
    | _ChoicesMapping
    | type[Choices]
    | Callable[[], _Choices | _ChoicesMapping]
)

class RangeField(forms.MultiValueField):
    widget: _ClassLevelWidget = ...
    def __init__(
        self,
        fields: tuple[forms.Field, forms.Field] | None = None,
        *,
        require_all_fields: bool = True,
        required: bool = ...,
        widget: Widget | type[Widget] | None = ...,
        label: StrOrPromise | None = ...,
        initial: Any | None = ...,
        help_text: StrOrPromise = ...,
        error_messages: Mapping[str, StrOrPromise] | None = ...,
        show_hidden_initial: bool = ...,
        validators: Sequence[_ValidatorCallable] = ...,
        localize: bool = ...,
        disabled: bool = ...,
        label_suffix: str | None = ...,
    ) -> None: ...
    def compress(self, data_list: list[Any] | None) -> slice | None: ...

class DateRangeField(RangeField):
    widget: _ClassLevelWidget = ...
    def compress(self, data_list: list[Any] | None) -> slice | None: ...

class DateTimeRangeField(RangeField):
    widget: _ClassLevelWidget = ...

class IsoDateTimeRangeField(RangeField):
    widget: _ClassLevelWidget = ...

class TimeRangeField(RangeField):
    widget: _ClassLevelWidget = ...

class Lookup(NamedTuple):
    value: Any
    lookup_expr: str

class LookupChoiceField(forms.MultiValueField):
    def __init__(
        self,
        field: forms.Field,
        lookup_choices: Sequence[tuple[str, str]],
        *,
        empty_label: StrOrPromise = ...,
        widget: Unused = ...,
        help_text: Unused = ...,
        require_all_fields: bool = True,
        required: bool = ...,
        label: StrOrPromise | None = ...,
        initial: Any | None = ...,
        error_messages: Mapping[str, StrOrPromise] | None = ...,
        show_hidden_initial: bool = ...,
        validators: Sequence[_ValidatorCallable] = ...,
        localize: bool = ...,
        disabled: bool = ...,
        label_suffix: str | None = ...,
    ) -> None: ...
    def compress(self, data_list: list[Any] | None) -> Lookup | None: ...

class IsoDateTimeField(forms.DateTimeField):
    ISO_8601: str
    input_formats: list[str]
    def strptime(self, value: str, format: str) -> Any: ...

class BaseCSVField(forms.Field):
    base_widget_class: _ClassLevelWidget = ...
    def clean(self, value: Any) -> Any: ...

class BaseRangeField(BaseCSVField):
    widget: _ClassLevelWidget = ...
    def clean(self, value: Any) -> Any: ...

class ChoiceIterator:
    field: ChoiceField
    choices: Sequence[tuple[Any, str]]
    def __init__(
        self,
        field: ChoiceField,
        choices: Sequence[tuple[Any, str]],
    ) -> None: ...
    def __iter__(self) -> Any: ...
    def __len__(self) -> int: ...

class ModelChoiceIterator(forms.models.ModelChoiceIterator):
    def __iter__(self) -> Any: ...
    def __len__(self) -> int: ...

class ChoiceIteratorMixin:
    null_label: StrOrPromise | None
    null_value: Any
    def __init__(
        self,
        *,
        null_label: StrOrPromise | None,
        null_value: Any,
    ) -> None: ...

class ChoiceField(ChoiceIteratorMixin, forms.ChoiceField):
    iterator = ChoiceIterator
    empty_label: StrOrPromise
    def __init__(
        self,
        *,
        empty_label: StrOrPromise = ...,
        choices: _ChoicesInput = (),
        required: bool = ...,
        widget: Widget | type[Widget] | None = ...,
        label: StrOrPromise | None = ...,
        initial: Any | None = ...,
        help_text: StrOrPromise = ...,
        error_messages: Mapping[str, StrOrPromise] | None = ...,
        show_hidden_initial: bool = ...,
        validators: Sequence[_ValidatorCallable] = ...,
        localize: bool = ...,
        disabled: bool = ...,
        label_suffix: str | None = ...,
        null_label: StrOrPromise | None,
        null_value: Any,
    ) -> None: ...

class MultipleChoiceField(ChoiceIteratorMixin, forms.MultipleChoiceField):
    iterator = ChoiceIterator
    empty_label: StrOrPromise | None

class ModelChoiceField(ChoiceIteratorMixin, forms.ModelChoiceField[Any]):
    iterator = ModelChoiceIterator
    def to_python(self, value: Any) -> Any: ...

class ModelMultipleChoiceField(
    ChoiceIteratorMixin,
    forms.ModelMultipleChoiceField[Any],
):
    iterator = ModelChoiceIterator
