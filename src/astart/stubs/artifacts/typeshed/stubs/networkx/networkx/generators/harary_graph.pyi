from networkx.utils.backends import _dispatchable

__all__ = ["hkn_harary_graph", "hnm_harary_graph"]

@_dispatchable
def hnm_harary_graph(n, m, create_using=None): ...
@_dispatchable
def hkn_harary_graph(k, n, create_using=None): ...
