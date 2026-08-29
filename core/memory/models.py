"""
core/memory/models.py

Session 7 brick (Milestone C): the in-code shape of the Project Constitution.

The Constitution is the project's single source of truth (AI_Project_Execution_
Engine.md, Section 2). These 13 fields are captured verbatim from that document.
It is stored as JSONB in the `constitutions` table (see infra/migrations/
0001_init.sql) and persisted **append-only, versioned** — every change is a new
row / a new entry in `change_history`, never an in-place overwrite (Section 2's
load-bearing rule). The versioning + persistence logic is the repository's job
(Session 8); this module is just the validated data shape.

Pydantic (per the tech-stack choice, Master Construction Spec Part IV) gives us
validation + clean JSON round-tripping to/from the JSONB column.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Constitution(BaseModel):
    """The 13-section Project Constitution (AI_Project_Execution_Engine.md §2).

    All fields default to empty so a Constitution can be created early and
    filled in as the intake (Section 1) and research (Sections 5-7) proceed.
    List fields hold labeled items; `change_history` is append-only and owned
    by the repository, not edited directly by callers.
    """

    mission: str = ""
    purpose: str = ""
    desired_outcome: str = ""
    success_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    non_negotiables: list[str] = Field(default_factory=list)
    available_resources: list[str] = Field(default_factory=list)
    known_facts: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    change_history: list[str] = Field(default_factory=list)
