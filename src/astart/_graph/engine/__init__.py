"""Clean, from-scratch graph inference engine.

``FromScratchBackend`` is a soundness-first source-to-source inference engine:
it annotates parameters, return types, and instance attributes from direct
evidence and falls back to ``object`` when evidence is insufficient, so the
output is always internally consistent under a strict type checker.
"""

from astart._graph.engine.backend import FromScratchBackend

__all__: list[str] = ["FromScratchBackend"]
