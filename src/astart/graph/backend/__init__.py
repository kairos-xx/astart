"""Graph-inference backend, organized as an OOP package.

``CheckpointBackend`` is the current strongest source-to-source inference
engine. It implements the :class:`InferenceBackend` protocol and composes the
``engine``, ``refiner``, and ``finalizer`` modules into discrete pipeline
phases.

"""

from astart.graph.backend.checkpoint import CheckpointBackend
from astart.graph.backend.interfaces import InferenceBackend

__all__: list[str] = ["CheckpointBackend", "InferenceBackend"]
