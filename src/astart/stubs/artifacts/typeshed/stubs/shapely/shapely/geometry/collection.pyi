from collections.abc import Collection
from typing import Self, overload

from .._typing import OptGeoArrayLike
from .base import BaseMultipartGeometry, GeometrySequence, _GeoT_co

class GeometryCollection(BaseMultipartGeometry[_GeoT_co]):
    __slots__: list[str] = []
    @overload
    def __new__(
        self,
        geoms: BaseMultipartGeometry[_GeoT_co]
        | GeometrySequence[BaseMultipartGeometry[_GeoT_co]]
        | Collection[_GeoT_co],
    ) -> Self: ...
    @overload
    def __new__(self, geoms: OptGeoArrayLike = None) -> Self: ...
    @property
    def boundary(self) -> None: ...
