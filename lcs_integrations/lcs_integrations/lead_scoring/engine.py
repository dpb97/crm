"""Rule-based lead scoring engine.

Framework-agnostic: `score(lead_dict, rules)` takes a plain dict and a list
of rule dicts and returns the integer score. This lets unit tests run without
a Frappe site.
"""

from __future__ import annotations

from typing import Any, Iterable


_Operator = str


def _evaluate(field_value: Any, operator: _Operator, target: str) -> bool:
    if operator == "eq":
        return str(field_value) == target
    if operator == "neq":
        return str(field_value) != target
    if operator == "in":
        return str(field_value) in {v.strip() for v in target.split(",")}
    if operator == "not_in":
        return str(field_value) not in {v.strip() for v in target.split(",")}
    if operator == "contains":
        return target.lower() in str(field_value or "").lower()
    if operator == "gt":
        try:
            return float(field_value) > float(target)
        except (TypeError, ValueError):
            return False
    if operator == "lt":
        try:
            return float(field_value) < float(target)
        except (TypeError, ValueError):
            return False
    return False


def score(lead: dict[str, Any], rules: Iterable[dict[str, Any]]) -> int:
    total = 0
    for rule in sorted(rules, key=lambda r: -int(r.get("priority", 0))):
        if not rule.get("active", True):
            continue
        value = lead.get(rule["field_name"])
        if _evaluate(value, rule["operator"], rule["value"]):
            total += int(rule["score_delta"])
    return total
