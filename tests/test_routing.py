"""
Tests for core.models.routing — proves policy-based routing without any real
API key or network call (verification level 2). The Session 4 acceptance
criterion is the first test: the same task type under two policies resolves to
two different logical names.
"""

from __future__ import annotations

import logging

from core.models.registry import DEFAULT_LOGICAL_MODEL, LOGICAL_MODEL_NAMES
from core.models.routing import POLICIES, route


def test_same_task_different_policies_route_to_different_logical_names():
    # Session 4 acceptance: cheap vs quality on the same task -> different names.
    cheap = route("general", "cheap")
    quality = route("general", "quality")
    assert cheap != quality
    assert cheap == "cheap-fast"
    assert quality == "reasoning-strong"


def test_every_policy_routes_to_a_registered_logical_name():
    for task_type in ("general", "code"):
        for policy in POLICIES:
            assert route(task_type, policy) in LOGICAL_MODEL_NAMES


def test_unknown_task_type_falls_back_to_general_row():
    # An unlisted task type behaves like `general` for the same policy.
    assert route("totally-unknown-task", "cheap") == route("general", "cheap")


def test_unknown_policy_falls_back_to_default_logical_model():
    assert route("general", "not-a-policy") == DEFAULT_LOGICAL_MODEL


def test_code_task_prefers_coding_model_on_balanced():
    assert route("code", "balanced") == "coding"


def test_route_logs_the_decision(caplog):
    with caplog.at_level(logging.INFO, logger="core.models.routing"):
        route("general", "balanced")
    joined = " ".join(caplog.messages)
    assert "routing decision" in joined
    assert "policy=balanced" in joined
    assert "logical_model=reasoning-strong" in joined
