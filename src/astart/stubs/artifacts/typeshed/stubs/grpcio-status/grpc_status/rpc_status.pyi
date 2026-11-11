import grpc

from . import _async as aio

def from_call(call: grpc.Call): ...
def to_status(status) -> grpc.Status: ...

__all__ = ["aio", "from_call", "to_status"]
