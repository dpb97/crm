"""Unit tests for the framework-agnostic scoring engine.

The engine intentionally has no Frappe dependency, so these tests run in
plain pytest without any stub.
"""

from __future__ import annotations

import pytest

from lcs_integrations.lead_scoring.engine import score


def _rule(**overrides):
    base = {
        "field_name": "source",
        "operator": "eq",
        "value": "website",
        "score_delta": 10,
        "priority": 0,
        "active": True,
    }
    base.update(overrides)
    return base


def test_score_sums_matching_rules():
    lead = {"source": "website", "country": "AT"}
    rules = [
        _rule(field_name="source", operator="eq", value="website", score_delta=10),
        _rule(field_name="country", operator="eq", value="AT", score_delta=5),
    ]
    assert score(lead, rules) == 15


def test_inactive_rules_are_ignored():
    lead = {"source": "website"}
    rules = [_rule(active=False, score_delta=10)]
    assert score(lead, rules) == 0


def test_non_matching_rules_contribute_zero():
    lead = {"source": "cold_call"}
    rules = [_rule(score_delta=10)]
    assert score(lead, rules) == 0


@pytest.mark.parametrize(
    ("operator", "target", "field_value", "expected"),
    [
        ("eq", "x", "x", True),
        ("eq", "x", "y", False),
        ("neq", "x", "y", True),
        ("neq", "x", "x", False),
        ("in", "a,b,c", "b", True),
        ("in", "a,b,c", "d", False),
        ("not_in", "a,b,c", "d", True),
        ("not_in", "a,b,c", "a", False),
        ("contains", "part", "this is a partial match", True),
        ("contains", "part", None, False),
        ("gt", "10", 15, True),
        ("gt", "10", 5, False),
        ("gt", "10", "not a number", False),
        ("lt", "10", 5, True),
        ("lt", "10", 15, False),
        ("unknown_operator", "x", "x", False),
    ],
)
def test_operators(operator, target, field_value, expected):
    lead = {"f": field_value}
    rules = [_rule(field_name="f", operator=operator, value=target, score_delta=1)]
    assert score(lead, rules) == (1 if expected else 0)


def test_priority_does_not_change_sum_but_is_stable():
    lead = {"f": "x"}
    rules = [
        _rule(field_name="f", operator="eq", value="x", score_delta=3, priority=1),
        _rule(field_name="f", operator="eq", value="x", score_delta=7, priority=5),
    ]
    # Sum is order-independent but we assert it explicitly so a regression
    # that drops entries during sort is caught.
    assert score(lead, rules) == 10


def test_missing_field_returns_zero():
    # The lead dict does not carry the field the rule asks for — must not raise.
    lead = {}
    rules = [_rule(field_name="missing", operator="eq", value="x")]
    assert score(lead, rules) == 0


def test_default_active_when_unset():
    lead = {"source": "website"}
    rule = {"field_name": "source", "operator": "eq", "value": "website", "score_delta": 4}
    assert score(lead, [rule]) == 4
