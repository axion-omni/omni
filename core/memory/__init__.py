"""
core/memory — persistent project state (Milestone C onward).

This package owns everything that must survive a process restart or a cloud
redeploy: the Project Constitution first (Session 7-9), then decisions,
research, and the task graph in later milestones. Access goes through a thin
repository layer over PostgreSQL so the storage engine stays swappable
(Master Construction Specification, Part XXII).

Session 6 provides only the database access seam (db.py) and the memory-layer
exception hierarchy — no schema, no tables yet.
"""
