from typing import Any

from _typeshed import Unused
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponse
from django.views.generic import View
from django.views.generic.list import (
    MultipleObjectMixin,
    MultipleObjectTemplateResponseMixin,
)

from .constants import ALL_FIELDS
from .filterset import FilterSet

class FilterMixin:
    filterset_class: type[FilterSet] | None
    filterset_fields = ALL_FIELDS
    strict: bool
    def get_filterset_class(self) -> type[FilterSet] | None: ...
    def get_filterset(self, filterset_class: type[FilterSet]) -> FilterSet: ...
    def get_filterset_kwargs(
        self,
        filterset_class: type[FilterSet],
    ) -> dict[str, Any]: ...
    def get_strict(self) -> bool: ...

class BaseFilterView(FilterMixin, MultipleObjectMixin[Any], View):
    filterset: FilterSet
    object_list: QuerySet[Any]
    def get(
        self,
        request: HttpRequest,
        *args: Unused,
        **kwargs: Unused,
    ) -> HttpResponse: ...

class FilterView(MultipleObjectTemplateResponseMixin, BaseFilterView):
    template_name_suffix: str

def object_filter(
    request: HttpRequest,
    model: type[Model] | None = None,
    queryset: QuerySet[Any] | None = None,
    template_name: str | None = None,
    extra_context: dict[str, Any] | None = None,
    context_processors: list[Any] | None = None,
    filter_class: type[FilterSet] | None = None,
) -> HttpResponse: ...
