from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest
from django_filters.filterset import FilterSetMetaclass

from . import filterset

type _APIView = Any

class DjangoFilterBackend:
    filterset_base: FilterSetMetaclass = ...
    raise_exception: bool
    @property
    def template(self) -> str: ...
    def get_filterset(
        self,
        request: HttpRequest,
        queryset: QuerySet[Any],
        view: _APIView,
    ) -> filterset.FilterSet | None: ...
    def get_filterset_class(
        self,
        view: _APIView,
        queryset: QuerySet[Any] | None = None,
    ) -> type[filterset.FilterSet] | None: ...
    def get_filterset_kwargs(
        self,
        request: HttpRequest,
        queryset: QuerySet[Any],
        view: _APIView,
    ) -> dict[str, Any]: ...
    def filter_queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet[Any],
        view: _APIView,
    ) -> QuerySet[Any]: ...
    def to_html(
        self,
        request: HttpRequest,
        queryset: QuerySet[Any],
        view: _APIView,
    ) -> str: ...
