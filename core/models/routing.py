"""
core/models/routing.py

Session 4 brick (Stage 2 — Model Abstraction & Routing): policy-based routing.

Turns a (task_type, MODEL_POLICY) pair into a *logical* model name that the
Model Registry (Session 3) then resolves to a concrete (provider, model_id).
Callers above this layer never name a model — they say what they're doing
(task_type) and how much they'll spend (policy), and routing + registry decide
the rest. This is the piece that makes MODEL_POLICY in .env actually change
behavior (Master Construction Spec Part VII Session 4; Part XIX cost policies).

The routing decision is logged (logger "core.models.routing"). That log line is
the observability hook Stage 16 will read, and the level-3 proof that flipping
MODEL_POLICY changed the selection.

Scope note: the table is deliberately small (a `general` row that is also the
fallback, plus a `code` row). Every logical name it can emit is a registered
LOGICAL_MODEL_NAME, validated at import. Because the Session 3 registry maps
every logical name to the active provider's single verified model today (D007),
two policies can select different logical names while resolving to the same
concrete model until a second model is registered — the routing decision still
changes, and the log line proves it. Retry/fallback is Session 5.
"""

from __future__ import annotations

import logging

from core.models.registry import DEFAULT_LOGICAL_MODEL, LOGICAL_MODEL_NAMES

logger = logging.getLogger("core.models.routing")

# The five cost policies (Master Construction Spec Part XIX), sourced from
# Settings.model_policy (env MODEL_POLICY).
POLICIES = ("free", "cheap", "balanced", "quality", "maximum")

DEFAULT_TASK_TYPE = "general"

# task_type -> (policy -> logical_name). `general` is the fallback row for any
# task_type not listed. Every value must be a registered LOGICAL_MODEL_NAME.
_ROUTING_TABLE: dict[str, dict[str, str]] = {
    "general": {
        "free": "cheap-fast",
        "cheap": "cheap-fast",
        "balanced": "reasoning-strong",
        "quality": "reasoning-strong",
        "maximum": "reasoning-strong",
    },
    "code": {
        "free": "cheap-fast",
        "cheap": "coding",
        "balanced": "coding",
        "quality": "coding",
        "maximum": "reasoning-strong",
    },
}


def _validate_table() -> None:
    """Fail fast at import if the table names a model the registry can't
    resolve — cheaper to catch here than as a runtime ModelNotRegisteredError."""
    for policy_map in _ROUTING_TABLE.values():
        for logical in policy_map.values():
            if logical not in LOGICAL_MODEL_NAMES:
                raise ValueError(
                    f"routing table names unknown logical model {logical!r}; "
                    f"known: {LOGICAL_MODEL_NAMES}"
                )


_validate_table()


def route(task_type: str, policy: str) -> str:
    """Resolve (task_type, policy) -> a logical model name.

    Unknown task_type falls back to the `general` row; unknown policy falls
    back to DEFAULT_LOGICAL_MODEL. Never raises — routing degrades to a safe
    default rather than crashing the caller.
    """
    policy_map = _ROUTING_TABLE.get(task_type, _ROUTING_TABLE[DEFAULT_TASK_TYPE])
    logical = policy_map.get(policy, DEFAULT_LOGICAL_MODEL)
    logger.info(
        "routing decision: task_type=%s policy=%s -> logical_model=%s",
        task_type,
        policy,
        logical,
    )
    return logical
