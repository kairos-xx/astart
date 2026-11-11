from _typeshed import Incomplete

class Options:
    __slots__ = (
        "deadline",
        "force_writes",
        "global_cache_timeout",
        "max_memcache_items",
        "memcache_timeout",
        "propagation",
        "retries",
        "timeout",
        "use_cache",
        "use_datastore",
        "use_global_cache",
        "use_memcache",
    )
    @classmethod
    def options(
        cls,
        wrapped,
        _disambiguate_from_model_properties: bool = ...,
    ): ...
    @classmethod
    def slots(cls): ...
    def __init__(self, config: Incomplete | None = ..., **kwargs) -> None: ...
    def __eq__(self, other): ...
    def __ne__(self, other): ...
    def copy(self, **kwargs): ...
    def items(self) -> None: ...

class ReadOptions(Options):
    __slots__ = ("read_consistency", "read_policy", "transaction")
    def __init__(self, config: Incomplete | None = ..., **kwargs) -> None: ...
