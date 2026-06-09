"""Shared pytest fixtures.

These tests are **framework-free** — they never import the real `frappe`
module. Any module that touches `frappe` should be imported lazily inside
a fixture or after the stub has been registered, so that `pytest` can run
without a Frappe site.
"""

from __future__ import annotations

import sys
import types
from collections.abc import Iterator
from typing import Any

import pytest


class _FrappeFlags(dict):
    """Dict that mimics `frappe.flags` — supports attribute-style access."""

    def __getattr__(self, item: str) -> Any:
        return self.get(item)

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


@pytest.fixture
def frappe_stub(monkeypatch: pytest.MonkeyPatch) -> Iterator[types.ModuleType]:
    """Install a minimal `frappe` stub that satisfies the modules under test.

    Extend the stub inside individual tests via `monkeypatch.setattr` when
    more surface is needed — keep the baseline lean so missing attributes
    surface as AttributeError (explicit over implicit).
    """
    stub = types.ModuleType("frappe")
    stub.flags = _FrappeFlags()  # type: ignore[attr-defined]
    stub.get_all = lambda *_args, **_kwargs: []  # type: ignore[attr-defined]
    stub.db = types.SimpleNamespace(  # type: ignore[attr-defined]
        set_value=lambda *_args, **_kwargs: None,
        exists=lambda *_args, **_kwargs: False,
        commit=lambda: None,
    )

    def _whitelist(*_args: Any, **_kwargs: Any):  # pragma: no cover - trivial
        def _decorator(func):
            return func

        return _decorator if _args and not callable(_args[0]) else _args[0]

    stub.whitelist = _whitelist  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "frappe", stub)
    yield stub
