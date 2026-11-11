from collections.abc import Callable, Iterable
from typing import Any

from django import forms
from django.db.models import QuerySet
from django.forms import Field
from django_stubs_ext import StrOrPromise

from .fields import (
    BaseCSVField,
    BaseRangeField,
    DateRangeField,
    DateTimeRangeField,
    IsoDateTimeField,
    IsoDateTimeRangeField,
    Lookup,
    LookupChoiceField,
    ModelChoiceField,
    ModelMultipleChoiceField,
    RangeField,
    TimeRangeField,
)

__all__ = [
    "AllValuesFilter",
    "AllValuesMultipleFilter",
    "BaseCSVFilter",
    "BaseInFilter",
    "BaseRangeFilter",
    "BooleanFilter",
    "CharFilter",
    "ChoiceFilter",
    "DateFilter",
    "DateFromToRangeFilter",
    "DateRangeFilter",
    "DateTimeFilter",
    "DateTimeFromToRangeFilter",
    "DurationFilter",
    "Filter",
    "IsoDateTimeFilter",
    "IsoDateTimeFromToRangeFilter",
    "LookupChoiceFilter",
    "ModelChoiceFilter",
    "ModelMultipleChoiceFilter",
    "MultipleChoiceFilter",
    "NumberFilter",
    "NumericRangeFilter",
    "OrderingFilter",
    "RangeFilter",
    "TimeFilter",
    "TimeRangeFilter",
    "TypedChoiceFilter",
    "TypedMultipleChoiceFilter",
    "UUIDFilter",
]

class Filter:
    creation_counter: int
    field_class: type[Any]
    field_name: str | None
    lookup_expr: str
    distinct: bool
    exclude: bool
    extra: dict[str, Any]
    def __init__(
        self,
        field_name: str | None = None,
        lookup_expr: str | None = None,
        *,
        label: StrOrPromise | None = None,
        method: Callable[..., Any] | str | None = None,
        distinct: bool = False,
        exclude: bool = False,
        **kwargs: Any,
    ) -> None: ...
    def get_method(
        self,
        qs: QuerySet[Any],
    ) -> Callable[..., QuerySet[Any]]: ...
    method: Callable[..., Any] | str | None
    label: StrOrPromise | None
    @property
    def field(self) -> Field: ...
    def filter(self, qs: QuerySet[Any], value: Any) -> QuerySet[Any]: ...

class CharFilter(Filter):
    field_class: type[forms.CharField]

class BooleanFilter(Filter):
    field_class: type[forms.NullBooleanField]

class ChoiceFilter(Filter):
    field_class: type[Any]
    null_value: Any
    def __init__(
        self,
        field_name: str | None = None,
        lookup_expr: str | None = None,
        *,
        null_value: Any = ...,
        label: StrOrPromise | None = None,
        method: Callable[..., Any] | str | None = None,
        distinct: bool = False,
        exclude: bool = False,
        **kwargs: Any,
    ) -> None: ...
    def filter(self, qs: QuerySet[Any], value: Any) -> QuerySet[Any]: ...

class TypedChoiceFilter(Filter):
    field_class: type[forms.TypedChoiceField]

class UUIDFilter(Filter):
    field_class: type[forms.UUIDField]

class MultipleChoiceFilter(Filter):
    field_class: type[Any]
    always_filter: bool
    conjoined: bool
    null_value: Any
    def __init__(
        self,
        field_name: str | None = None,
        lookup_expr: str | None = None,
        *,
        distinct: bool = True,
        conjoined: bool = False,
        null_value: Any = ...,
        label: StrOrPromise | None = None,
        method: Callable[..., Any] | str | None = None,
        exclude: bool = False,
        **kwargs: Any,
    ) -> None: ...
    def is_noop(self, qs: QuerySet[Any], value: Any) -> bool: ...
    def filter(self, qs: QuerySet[Any], value: Any) -> QuerySet[Any]: ...
    def get_filter_predicate(self, v: Any) -> dict[str, Any]: ...

class TypedMultipleChoiceFilter(MultipleChoiceFilter):
    field_class: type[forms.TypedMultipleChoiceField]

class DateFilter(Filter):
    field_class: type[forms.DateField]

class DateTimeFilter(Filter):
    field_class: type[forms.DateTimeField]

class IsoDateTimeFilter(DateTimeFilter):
    field_class: type[IsoDateTimeField]

class TimeFilter(Filter):
    field_class: type[forms.TimeField]

class DurationFilter(Filter):
    field_class: type[forms.DurationField]

class QuerySetRequestMixin:
    queryset: QuerySet[Any] | None
    def __init__(self, *, queryset: QuerySet[Any] | None) -> None: ...
    def get_request(self) -> Any: ...
    def get_queryset(self, request: Any) -> QuerySet[Any]: ...
    @property
    def field(self) -> Field: ...

class ModelChoiceFilter(QuerySetRequestMixin, ChoiceFilter):
    field_class: type[ModelChoiceField]
    def __init__(
        self,
        field_name: str | None = None,
        lookup_expr: str | None = None,
        *,
        queryset: QuerySet[Any] | None = None,
        null_value: Any = ...,
        label: StrOrPromise | None = None,
        method: Callable[..., Any] | str | None = None,
        distinct: bool = False,
        exclude: bool = False,
        **kwargs: Any,
    ) -> None: ...

class ModelMultipleChoiceFilter(QuerySetRequestMixin, MultipleChoiceFilter):
    field_class: type[ModelMultipleChoiceField]
    def __init__(
        self,
        field_name: str | None = None,
        lookup_expr: str | None = None,
        *,
        queryset: QuerySet[Any] | None = None,
        distinct: bool = True,
        conjoined: bool = False,
        null_value: Any = ...,
        label: StrOrPromise | None = None,
        method: Callable[..., Any] | str | None = None,
        exclude: bool = False,
        **kwargs: Any,
    ) -> None: ...

class NumberFilter(Filter):
    field_class: type[forms.DecimalField]
    def get_max_validator(self) -> Any: ...
    @property
    def field(self) -> Field: ...

class NumericRangeFilter(Filter):
    field_class: type[RangeField]
    lookup_expr: str
    def filter(self, qs: QuerySet[Any], value: Any) -> QuerySet[Any]: ...

class RangeFilter(Filter):
    field_class: type[RangeField]
    lookup_expr: str
    def filter(self, qs: QuerySet[Any], value: Any) -> QuerySet[Any]: ...

class DateRangeFilter(ChoiceFilter):
    choices: list[tuple[str, str]] | None
    filters: dict[str, Filter] | None
    def __init__(
        self,
        choices: list[tuple[str, str]] | None = None,
        filters: dict[str, Filter] | None = None,
        field_name: str | None = None,
        lookup_expr: str | None = None,
        *,
        null_value: Any = ...,
        label: StrOrPromise | None = None,
        method: Callable[..., Any] | str | None = None,
        distinct: bool = False,
        exclude: bool = False,
        **kwargs: Any,
    ) -> None: ...
    def filter(self, qs: QuerySet[Any], value: Any) -> QuerySet[Any]: ...

class DateFromToRangeFilter(RangeFilter):
    field_class: type[DateRangeField]

class DateTimeFromToRangeFilter(RangeFilter):
    field_class: type[DateTimeRangeField]

class IsoDateTimeFromToRangeFilter(RangeFilter):
    field_class: type[IsoDateTimeRangeField]

class TimeRangeFilter(RangeFilter):
    field_class: type[TimeRangeField]

class AllValuesFilter(ChoiceFilter):
    @property
    def field(self) -> Field: ...

class AllValuesMultipleFilter(MultipleChoiceFilter):
    @property
    def field(self) -> Field: ...

class BaseCSVFilter(Filter):
    base_field_class: type[BaseCSVField] = ...
    field_class: type[Any]

class BaseInFilter(BaseCSVFilter): ...

class BaseRangeFilter(BaseCSVFilter):
    base_field_class: type[BaseRangeField] = ...

class LookupChoiceFilter(Filter):
    field_class: type[forms.CharField]
    outer_class: type[LookupChoiceField] = ...
    empty_label: StrOrPromise | None
    lookup_choices: list[tuple[str, StrOrPromise]] | None
    def __init__(
        self,
        field_name: str | None = None,
        lookup_choices: list[tuple[str, StrOrPromise]] | None = None,
        field_class: type[Field] | None = None,
        *,
        empty_label: StrOrPromise = ...,
        label: StrOrPromise | None = None,
        method: Callable[..., Any] | str | None = None,
        distinct: bool = False,
        exclude: bool = False,
        **kwargs: Any,
    ) -> None: ...
    @classmethod
    def normalize_lookup(
        cls,
        lookup: str | tuple[str, StrOrPromise],
    ) -> tuple[str, StrOrPromise]: ...
    def get_lookup_choices(self) -> list[tuple[str, StrOrPromise]]: ...
    @property
    def field(self) -> Field: ...
    lookup_expr: str
    def filter(self, qs: QuerySet[Any], lookup: Lookup) -> QuerySet[Any]: ...

class OrderingFilter(BaseCSVFilter, ChoiceFilter):
    field_class: type[BaseCSVField]
    descending_fmt: str
    param_map: dict[str, str] | None
    def __init__(
        self,
        field_name: str | None = None,
        lookup_expr: str | None = None,
        *,
        fields: dict[str, str]
        | Iterable[str]
        | Iterable[tuple[str, str]] = ...,
        field_labels: dict[str, StrOrPromise] = ...,
        null_value: Any = ...,
        label: StrOrPromise | None = None,
        method: Callable[..., Any] | str | None = None,
        distinct: bool = False,
        exclude: bool = False,
        **kwargs: Any,
    ) -> None: ...
    def get_ordering_value(self, param: str) -> str: ...
    def filter(self, qs: QuerySet[Any], value: Any) -> QuerySet[Any]: ...
    @classmethod
    def normalize_fields(cls, fields: Any) -> list[str]: ...
    def build_choices(
        self,
        fields: Any,
        labels: dict[str, StrOrPromise] | None,
    ) -> list[tuple[str, str]]: ...

class FilterMethod:
    f: Filter
    def __init__(self, filter_instance: Filter) -> None: ...
    def __call__(self, qs: QuerySet[Any], value: Any) -> QuerySet[Any]: ...
    @property
    def method(self) -> Callable[..., Any]: ...
