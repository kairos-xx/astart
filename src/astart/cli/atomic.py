"""Atomic file replacement shared by the CLI commands."""

from __future__ import annotations

from astart.files import write_atomic

__all__: list[str] = ["write_atomic"]
