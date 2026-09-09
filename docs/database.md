# Lenny Growth Assistant — Database & Persistence Architecture

**Document Version:** 1.0.0  
**Status:** Persistence & API Layer Complete (Phase 4)  
**Author:** Senior Forward Deployed Engineer & AI Systems Architect  

---

## 1. Overview & Architecture

The persistence architecture of **The Lenny Growth Assistant** is built upon PostgreSQL 16 with the `pgvector` extension. The database provides a unified, ACID-compliant storage engine for both **relational conversational entities** (chat sessions, messages, artifacts, users) and **high-dimensional knowledge base entities** (episodes, transcript chunks, embeddings, source citations).

```
+-------------------------------------------------------------------------------+
|                      POSTGRESQL UNIFIED PERSISTENCE                           |
+-------------------------------------------------------------------------------+
|  CONVERSATIONAL ENTITIES          |  KNOWLEDGE BASE ENTITIES                  |
|  - sessions (UUID, title, meta)   |  - episodes (title, guest, url)           |
|  - messages (session_id, role)    |  - transcript_chunks (embedding vector)   |
|  - artifacts (session_id, content)|  - message_sources (relevance citations)  |
|  - users (id, email, metadata)    |                                           |
+-------------------------------------------------------------------------------+
```

---

## 2. Relational Schema & Table Definitions

### 2.1 `sessions`
* `id` (`UUID`, Primary Key)
* `user_id` (`UUID`, Foreign Key $\rightarrow$ `users.id` on delete CASCADE, Nullable)
* `title` (`VARCHAR(255)`, Default: `'New Conversation'`)
* `metadata` (`JSONB`, Default: `{}`)
* `created_at` (`TIMESTAMPTZ`, Default: `NOW()`)
* `updated_at` (`TIMESTAMPTZ`, Default: `NOW()`, Index)

### 2.2 `messages`
* `id` (`UUID`, Primary Key)
* `session_id` (`UUID`, Foreign Key $\rightarrow$ `sessions.id` on delete CASCADE, Index)
* `role` (`VARCHAR(32)`: `'user' | 'assistant' | 'system'`)
* `content` (`TEXT`, Non-empty validated string)
* `tool_calls` (`JSONB`, Nullable)
* `metadata` (`JSONB`, Default: `{}`)
* `created_at` (`TIMESTAMPTZ`, Default: `NOW()`, Index)

### 2.3 `artifacts`
* `id` (`UUID`, Primary Key)
* `session_id` (`UUID`, Foreign Key $\rightarrow$ `sessions.id` on delete CASCADE, Index)
* `message_id` (`UUID`, Foreign Key $\rightarrow$ `messages.id` on delete SET NULL, Nullable)
* `title` (`VARCHAR(255)`)
* `artifact_type` (`VARCHAR(32)`: `'markdown' | 'html' | 'svg'`)
* `content` (`TEXT`, Sanitized artifact code)
* `version` (`INTEGER`, Default: `1`)
* `metadata` (`JSONB`, Default: `{}`)
* `created_at` (`TIMESTAMPTZ`)
* `updated_at` (`TIMESTAMPTZ`)

### 2.4 `episodes`
* `id` (`UUID`, Primary Key)
* `title` (`VARCHAR(512)`)
* `guest_name` (`VARCHAR(255)`, Index)
* `guest_role` (`VARCHAR(255)`, Nullable)
* `episode_url` (`VARCHAR(1024)`, Nullable)
* `publication_date` (`DATE`, Nullable)
* `duration_seconds` (`INTEGER`, Nullable)
* `metadata` (`JSONB`)
* `created_at` (`TIMESTAMPTZ`)

### 2.5 `transcript_chunks`
* `id` (`UUID`, Primary Key)
* `episode_id` (`UUID`, Foreign Key $\rightarrow$ `episodes.id` on delete CASCADE, Index)
* `chunk_index` (`INTEGER`)
* `chunk_text` (`TEXT`)
* `token_count` (`INTEGER`)
* `start_timestamp` (`VARCHAR(32)`, Nullable)
* `end_timestamp` (`VARCHAR(32)`, Nullable)
* `embedding` (`vector(384)` / `vector(1536)`, Vector Index)
* `metadata` (`JSONB`)
* `created_at` (`TIMESTAMPTZ`)

---

## 3. Database Migrations (Alembic Runbook)

Alembic manages all schema lifecycle events located in `backend/alembic/`.

### Run Pending Migrations:
```bash
cd backend
alembic upgrade head
```

### Roll Back Previous Migration:
```bash
cd backend
alembic downgrade -1
```

### Check Current Revision:
```bash
cd backend
alembic current
```

---

## 4. Repositories & Service Boundaries

The backend implements a strict two-tier data access pattern:
1. **Repository Layer (`backend/app/repositories/`):** Encapsulates raw SQLAlchemy queries and transactional operations (`SessionRepository`, `MessageRepository`). Does NOT contain HTTP or agent routing logic.
2. **Service Layer (`backend/app/services/`):** Coordinates business logic, validates cross-entity boundaries, and translates DB errors into domain exceptions (`SessionService`, `MessageService`, `ArtifactService`).

---

## 5. Session Isolation & Foreign Key Integrity

* **Zero Cross-Session Leakage:** Message queries filter strictly by `session_id` (`WHERE messages.session_id = :session_id`).
* **Cascade Deletion:** Deleting a `Session` automatically cascades to delete all its child `Message` and `Artifact` records, preventing orphaned data.
* **Deterministic Ordering:** Messages are ordered chronologically (`ORDER BY created_at ASC`).

---
*End of Database Documentation.*

