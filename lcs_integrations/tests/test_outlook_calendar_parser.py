"""Parser tests for the Graph datetime helper used by calendar sync."""

from __future__ import annotations

import pytest


@pytest.fixture
def cal_module(frappe_stub):
    from lcs_integrations.outlook_sync import calendar_sync

    return calendar_sync


def test_parse_graph_dt_strips_t_separator(cal_module):
    out = cal_module._parse_graph_dt({"dateTime": "2026-05-04T09:30:00.0000000", "timeZone": "UTC"})
    assert out == "2026-05-04 09:30:00"


def test_parse_graph_dt_handles_no_fractions(cal_module):
    out = cal_module._parse_graph_dt({"dateTime": "2026-05-04T09:30:00", "timeZone": "UTC"})
    assert out == "2026-05-04 09:30:00"


def test_parse_graph_dt_returns_none_on_missing_node(cal_module):
    assert cal_module._parse_graph_dt(None) is None
    assert cal_module._parse_graph_dt({}) is None
