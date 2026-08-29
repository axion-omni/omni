# Milestone E — Memory + RAG on pgvector (Deterministic Build Spec)

> **How to use this file.** Sessions run top to bottom; each is one brick
> (implement → L2 test → operator L3 → update the six docs + progress.json →
> commit). Labels E1… map to the next global `S<n>`. Code + CONTRACTS win over
> this spec; update and log a decision if they diverge. Grounded in: destination
> §7 (memory architecture), §2 (worked example), §11 (isolation); Construction
> Spec Part IV (Stage 4), Part XI (project memory).

> **Capability after this milestone:** ask a question about documents you’ve
> ingested and get a **grounded, cited** answer — from the phone (once D is done).

## Definition of done (authoritative gate)
Destination §15 Milestone E: **“A question about ingested documents gets a
grounded, cited phone reply.”** Construction Spec Stage 4: “A real question about
your own documents gets a grounded answer with a citation.” Verified L3 from phone.

## Prerequisites
- **Milestone C at L3** (Postgres) and **D at L3** (phone path).
- **pgvector enabled** on the database (the dev image already has it; on Supabase
  run `create extension if not exists vector;` — add it as migration `0002`).
- An **embeddings source**: an embeddings-capable API key (OpenAI/Voyage/etc.) or
  a local embedding model. Decide in E1.

## New dependencies / config / secrets
- `pgvector` Python adapter (or store vectors via raw SQL + `vector` type).
- Embeddings provider config: `EMBEDDINGS_PROVIDER`, `EMBEDDINGS_MODEL`, key.
- Config: `RAG_TOP_K` (default 5), `RAG_CHUNK_TOKENS`.

## Contracts introduced (add to CONTRACTS.md as built)
- `core/memory/embeddings.py`: `embed(texts: list[str], settings) -> list[Vector]`
  (provider behind a seam, like model providers).
- `core/memory/rag.py`: `ingest(project_id, doc_id, text, settings)`,
  `retrieve(project_id, query, settings, k=RAG_TOP_K) -> list[Chunk]` where each
  `Chunk` carries `text`, `source`, `score` (citations require `source`).
- Migration `0002_documents.sql`: `documents` + `chunks(embedding vector(N),
  project_id, source, text)` with an ivfflat/hnsw index; per-project scoped.

## Likely decisions to log (DECISIONS.md)
- **D0xx — embeddings provider** (which model, dimension N) behind a seam so it’s
  swappable (like model providers). Keep the DB driver rule: pgvector SQL only in
  `core/memory/`.
- **D0xx — chunking policy** (size/overlap) and **retrieval params** (k, index type).

## Sessions

### Session E1 — Embeddings seam
- **Goal:** turn text into vectors behind a provider-agnostic seam.
- **Files:** `core/memory/embeddings.py` (+ provider impl under
  `core/memory/embeddings_providers/` mirroring the model-provider layout);
  config; `tests/test_embeddings.py`.
- **Test gate (L2):** `embed` returns fixed-dimension vectors via an **injected
  fake** provider; dimension mismatch raises; no network.
- **Operator L3:** real key → embeds a sample, correct dimension.
- **Commit:** `feat: Session <n> - embeddings seam (Milestone E)`.

### Session E2 — Vector schema + migration (pgvector)
- **Goal:** tables to hold chunks + embeddings.
- **Files:** `infra/migrations/0002_documents.sql` (enable `vector`; `documents`,
  `chunks` with `vector(N)`, per-project scoped, similarity index);
  `tests/test_schema.py` extended.
- **Test gate (L2):** migration discovered + `pending()` includes it; live apply
  skips without DB.
- **Operator L3:** `python infra/migrate.py` creates the tables + index.
- **Commit:** `feat: Session <n> - documents/chunks pgvector schema`.

### Session E3 — Ingestion pipeline (chunk → embed → store)
- **Goal:** load a document into per-project memory.
- **Files:** `core/memory/rag.py::ingest`, chunker in `core/memory/chunking.py`;
  `tests/test_rag_ingest.py`.
- **Test gate (L2):** chunking splits deterministically; `ingest` writes chunks
  with `source` via an injected fake store + fake embedder (no DB/network).
- **Operator L3:** ingest a real doc into the dev DB; rows present.
- **Commit:** `feat: Session <n> - RAG ingestion pipeline`.

### Session E4 — Retrieval + grounded answer with citations
- **Goal:** answer a question using retrieved context, returning citations.
- **Files:** `core/memory/rag.py::retrieve`; an `answer_with_context()` that
  builds a grounded prompt (retrieved chunks + question) and calls the model
  pipeline; `tests/test_rag_retrieve.py`.
- **Test gate (L2):** retrieve ranks by similarity (fake store returns scored
  chunks); the built prompt includes sources; the answer surfaces citations.
- **Operator L3:** local end-to-end: ingest → ask → grounded cited answer.
- **Commit:** `feat: Session <n> - RAG retrieval + grounded cited answers`.

### Session E5 — Wire into the phone path + summarize-on-close
- **Goal:** ask from Telegram; keep memory small (summarize closed items before
  embedding, Part XI).
- **Files:** extend the webhook to route document questions through RAG;
  `tests/test_api_webhook.py` extended.
- **Test gate (L2):** an authorized “ask about my docs” update triggers retrieve
  + grounded reply (faked); citations present in the reply.
- **Operator L3 — THE GATE:** from the phone, ask about an ingested document →
  grounded, cited reply. Milestone E done.
- **Commit:** `feat: Session <n> - RAG on the phone path (Milestone E done)`.

## Security / deploy-safety notes
- **Per-project isolation**: every query filters by `project_id` (§11). A test
  must prove project A never retrieves project B’s chunks.
- Treat retrieved text as **untrusted data**, not instructions (prompt-injection).
- Index build on large tables is the deploy-safety surface — build concurrently.

## Explicitly deferred
- Tools/agents doing the asking autonomously → G/H. Cross-project knowledge → post-MVP.
