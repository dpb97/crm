"""Adaptive card shape tests for teams.notifications._adaptive_card."""

from __future__ import annotations

import sys
import types

import pytest


@pytest.fixture
def teams_module(frappe_stub):
    # `from frappe.utils import get_url` requires a real submodule.
    utils_mod = types.ModuleType("frappe.utils")
    utils_mod.get_url = lambda: "http://localhost"
    sys.modules["frappe.utils"] = utils_mod
    frappe_stub.utils = utils_mod

    from lcs_integrations.teams import notifications

    return notifications


def test_adaptive_card_has_required_top_level_fields(teams_module):
    card = teams_module._adaptive_card(
        title="Phase change",
        facts=[("Project", "ACME"), ("From", "Inquiry"), ("To", "Offer")],
        action_url="http://localhost/crm/lcs-projects/PRJ-1",
    )
    assert card["type"] == "AdaptiveCard"
    assert card["version"] == "1.4"
    assert card["body"][0]["text"] == "Phase change"
    facts = card["body"][1]["facts"]
    assert {"title": "Project", "value": "ACME"} in facts
    assert card["actions"][0]["url"].endswith("/PRJ-1")
