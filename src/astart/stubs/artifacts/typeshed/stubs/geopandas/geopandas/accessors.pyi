from typing import Any

import pandas as pd

class GeoSeriesAccessor:
    def __init__(self, series: pd.Series[Any]) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
