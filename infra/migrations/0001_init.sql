-- 0001_init.sql — Milestone C, Session 7. Initial persistent project state.
--
-- Applied by core/memory/migrations.py (forward-only). Safe to run repeatedly:
-- every statement is IF NOT EXISTS, and the runner records applied versions in
-- schema_migrations so it is not re-applied.
--
-- Design (D010): the Constitution is stored APPEND-ONLY and VERSIONED — one row
-- per version, never updated in place (AI_Project_Execution_Engine.md §2). Every
-- row is scoped by project_id for per-project data isolation (destination
-- architecture §11). gen_random_uuid() is built into PostgreSQL 13+ (the
-- pgvector:pg16 dev image and Supabase both satisfy this) — no extension needed.

CREATE TABLE IF NOT EXISTS projects (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS constitutions (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version     integer NOT NULL,
    content     jsonb NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (project_id, version)
);

CREATE INDEX IF NOT EXISTS idx_constitutions_project ON constitutions (project_id);
