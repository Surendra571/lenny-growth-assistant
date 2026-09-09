# The Lenny Growth Assistant — System Architecture Document

**Document Version:** 1.0.0  
**Status:** Architecture Baseline (Phase 2)  
**Author:** Senior Forward Deployed Engineer & AI Systems Architect  
**Project:** The Lenny Growth Assistant  
**Target Systems:** FastAPI, React/TypeScript, PostgreSQL + pgvector, Cloud LLM (Claude/OpenAI), Ollama  

---

## 1. System Overview

**The Lenny Growth Assistant** is an enterprise-grade agentic conversational application engineered to unlock the collective wisdom of *Lenny's Podcast* transcripts for product and growth practitioners.

The system is architected around six decoupled, highly cohesive subsystems:
1. **Frontend Presentation Layer (React / TypeScript / Tailwind CSS):** A responsive split-pane single-page application (SPA) featuring streaming chat rendering, interactive source attribution cards, session management, and a sandboxed side-by-side Artifact Studio.
2. **API & Routing Gateway (FastAPI):** High-performance asynchronous REST and Server-Sent Events (SSE) streaming gateway providing strict Pydantic payload validation, request-scoped context tracking, dependency injection, and centralized error handling.
3. **Application & Domain Service Layer:** Business orchestrators managing conversational session lifecycles, chat turn persistence, artifact revision tracking, and telemetry collection.
4. **Agent Orchestration & Skill Dispatcher:** A deterministic, tool-augmented agent layer responsible for intent classification, RAG retrieval orchestration, grounding verification, and routing to specialized skills (*Ship 30 for 30* writer, Markdown/HTML artifact generator).
5. **Knowledge & Hybrid Retrieval Subsystem:** A high-precision retrieval pipeline combining dense semantic vector embeddings (`pgvector`) with sparse BM25 keyword matching and Reciprocal Rank Fusion (RRF) across chunked podcast transcripts.
6. **Unified Persistence Layer (PostgreSQL with `pgvector`):** Single-database persistence handling relational tables (users, sessions, messages, artifacts, episode metadata) and vector indexes for high operational simplicity and ACID consistency.

---

## 2. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Client["Presentation Layer (Browser)"]
        UI["React 18 / TypeScript SPA"]
        ChatPane["Chat & Stream Controller"]
        SourceViewer["Source Citation Drawer"]
        ArtifactViewer["In-App Artifact Studio (Sandboxed iframe)"]
        UI --> ChatPane
        UI --> SourceViewer
        UI --> ArtifactViewer
    end

    subgraph Gateway["API & Gateway Layer (FastAPI)"]
        Router["FastAPI Gateway / CORS / Auth Middleware"]
        SessionAPI["/api/v1/sessions"]
        MessageAPI["/api/v1/sessions/{id}/messages (SSE)"]
        ArtifactAPI["/api/v1/artifacts"]
        HealthAPI["/health"]
        Router --> SessionAPI
        Router --> MessageAPI
        Router --> ArtifactAPI
        Router --> HealthAPI
    end

    subgraph ServiceLayer["Application Service Layer"]
        SessionSvc["Session Management Service"]
        ArtifactSvc["Artifact Storage & Sanitizer Service"]
        AgentSvc["Agent Orchestrator Service"]
        GuardrailSvc["Grounding & Refusal Guardrail"]
        SessionAPI --> SessionSvc
        ArtifactAPI --> ArtifactSvc
        MessageAPI --> AgentSvc
        AgentSvc --> GuardrailSvc
    end

    subgraph AgentLayer["Agent & Skill Engine"]
        AgentRouter["Agent Router & Intent Classifier"]
        QASkill["Grounded Q&A Skill"]
        Ship30Skill["Ship 30 for 30 Content Skill"]
        ArtifactSkill["Artifact Synthesis Skill"]
        
        AgentSvc --> AgentRouter
        AgentRouter --> QASkill
        AgentRouter --> Ship30Skill
        AgentRouter --> ArtifactSkill
    end

    subgraph RetrievalLayer["Knowledge & Retrieval Engine"]
        HybridRetriever["Hybrid Retriever (Dense + BM25)"]
        ReRanker["Reciprocal Rank Fusion (RRF)"]
        ChunkStore["Transcript Chunk Index"]
        QASkill --> HybridRetriever
        Ship30Skill --> HybridRetriever
        HybridRetriever --> ReRanker
        ReRanker --> ChunkStore
    end

    subgraph LLMProviders["Model Abstraction Layer"]
        LLMBase["LLMProvider (Abstract Base Class)"]
        CloudClient["CloudProvider (Anthropic Claude / OpenAI)"]
        OllamaClient["OllamaProvider (Local Llama 3.1 / Qwen 2.5)"]
        LLMBase --> CloudClient
        LLMBase --> OllamaClient
        QASkill --> LLMBase
        Ship30Skill --> LLMBase
        ArtifactSkill --> LLMBase
    end

    subgraph Persistence["Unified Persistence (PostgreSQL + pgvector)"]
        DB[(PostgreSQL 16)]
        T_Users["users"]
        T_Sessions["sessions"]
        T_Messages["messages"]
        T_Artifacts["artifacts"]
        T_Episodes["episodes"]
        T_Chunks["transcript_chunks (with vector embeddings)"]
        DB --- T_Users
        DB --- T_Sessions
        DB --- T_Messages
        DB --- T_Artifacts
        DB --- T_Episodes
        DB --- T_Chunks
    end

    ChatPane <==> |SSE Token Stream / JSON| MessageAPI
    SessionSvc --> DB
    ArtifactSvc --> DB
    ChunkStore --> T_Chunks
    T_Chunks --> T_Episodes
```

---

## 3. Component Boundaries & Responsibilities

| Component | Directory | Responsibilities | Dependencies | Forbidden Knowledge / Decoupling |
| :--- | :--- | :--- | :--- | :--- |
| **API Endpoints** | `backend/app/api/` | Route handling, HTTP status codes, request parsing, response serialization via Pydantic schemas, dependency injection. | Application Services, Pydantic Schemas | Must NOT contain raw SQL, LLM prompt strings, or direct model SDK calls. |
| **Core & Config** | `backend/app/core/` | Application settings, environment loading, structured logging, custom error types, security sanitizers. | `pydantic-settings`, standard library | Must NOT depend on business services or API routes. |
| **Data Models** | `backend/app/models/` | SQLAlchemy ORM declarative models, table schemas, indexes, foreign keys. | SQLAlchemy, pgvector | Must NOT contain business logic or API formatting. |
| **Schemas** | `backend/app/schemas/` | Pydantic validation models for requests, responses, events, and tool calls. | Pydantic | Must NOT depend on database connections or ORM session objects. |
| **Domain Services** | `backend/app/services/` | Session lifecycle orchestration, message history assembly, artifact persistence and sanitization. | DB Session, Models, Schemas | Must NOT handle HTTP transport details or raw frontend logic. |
| **Agent Engine** | `backend/app/agent/` | Intent routing, prompt assembly, skill dispatching, grounding verification, streaming tool calls. | LLM Provider abstraction, Retriever, Schemas | Must NOT depend directly on PostgreSQL engine or vendor-specific LLM SDKs. |
| **Knowledge / RAG** | `backend/app/knowledge/` | Text chunking, hybrid vector/keyword search, cosine similarity ranking, source metadata formatting. | DB Session, pgvector, Models | Must NOT know about frontend views or chat streaming protocol. |
| **LLM Providers** | `backend/app/agent/providers/` | Pluggable client adapters for Anthropic Claude, OpenAI, and local Ollama instances. | HTTP client (`httpx`), vendor SDKs | Must NOT contain business logic; only implements standard `LLMProvider` contract. |
| **Frontend UI** | `frontend/src/` | Interactive user interface, message state, SSE stream consumption, sandboxed iframe hosting. | React, Tailwind, Axios / fetch | Must NOT query database directly; only interacts via defined `/api/v1` contracts. |

---

## 4. Database Design & Entity Relationship Diagram

### 4.1 Relational & Vector Schema Overview

The database uses PostgreSQL 16 with the `pgvector` extension. All primary keys use `UUIDv4` for security and distributed ID generation. All timestamps are stored in UTC with timezone (`timestamptz`).

```mermaid
erDiagram
    users ||--o{ sessions : owns
    sessions ||--o{ messages : contains
    sessions ||--o{ artifacts : generates
    episodes ||--o{ transcript_chunks : divides_into
    messages ||--o{ message_sources : cites
    transcript_chunks ||--o{ message_sources : referenced_in

    users {
        uuid id PK
        string email
        jsonb metadata
        timestamptz created_at
        timestamptz updated_at
    }

    sessions {
        uuid id PK
        uuid user_id FK
        string title
        jsonb metadata
        timestamptz created_at
        timestamptz updated_at
    }

    messages {
        uuid id PK
        uuid session_id FK
        string role "user | assistant | system"
        text content
        jsonb tool_calls
        jsonb metadata
        timestamptz created_at
    }

    artifacts {
        uuid id PK
        uuid session_id FK
        uuid message_id FK
        string title
        string artifact_type "markdown | html | svg"
        text content
        integer version
        jsonb metadata
        timestamptz created_at
        timestamptz updated_at
    }

    episodes {
        uuid id PK
        string title
        string guest_name
        string guest_role
        string episode_url
        date publication_date
        integer duration_seconds
        jsonb metadata
        timestamptz created_at
    }

    transcript_chunks {
        uuid id PK
        uuid episode_id FK
        integer chunk_index
        text chunk_text
        integer token_count
        string start_timestamp
        string end_timestamp
        vector embedding "vector(1536) / vector(384)"
        jsonb metadata
        timestamptz created_at
    }

    message_sources {
        uuid id PK
        uuid message_id FK
        uuid chunk_id FK
        float relevance_score
        text snippet
        timestamptz created_at
    }
```

### 4.2 Indexes & Optimization
* `sessions(user_id, updated_at DESC)`: Fast session list retrieval.
* `messages(session_id, created_at ASC)`: Sequential conversation history loading.
* `artifacts(session_id, created_at DESC)`: Session artifact catalog query.
* `transcript_chunks(episode_id, chunk_index)`: Sequential chunk reassembly.
* `transcript_chunks USING hnsw (embedding vector_cosine_ops)`: High-performance approximate nearest neighbor (ANN) vector search.
* `transcript_chunks USING gin (to_tsvector('english', chunk_text))`: Full-text BM25 search index.

---

## 5. API Contracts & Communication Protocol

All endpoints are versioned under `/api/v1` except for system root `/health`.

### 5.1 System Health & Readiness
* **`GET /health`**
  * **Purpose:** Pre-flight service liveness check and active provider/model resolution.
  * **Response (200 OK):**
    ```json
    {
      "status": "ok",
      "service": "lenny-growth-assistant",
      "version": "1.0.0",
      "environment": "development",
      "llm_provider": "ollama",
      "active_model": "llama3.1:8b"
    }
    ```
* **`GET /ready`**
  * **Purpose:** Dependency readiness probe verifying PostgreSQL connectivity and LLM provider reachability.
  * **Response (200 OK):**
    ```json
    {
      "status": "ready",
      "database": "connected",
      "llm_provider": "ollama",
      "active_model": "llama3.1:8b",
      "llm_status": "connected"
    }
    ```

### 5.2 Session Management
* **`POST /api/v1/sessions`**
  * **Purpose:** Create a new conversation session.
  * **Request Body:** `{ "title": "Optional Custom Title" }` (or empty body for auto-titling)
  * **Response (201 Created):**
    ```json
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "title": "New Conversation",
      "created_at": "2026-09-09T13:15:00Z",
      "updated_at": "2026-09-09T13:15:00Z",
      "message_count": 0
    }
    ```
* **`GET /api/v1/sessions`**
  * **Purpose:** List recent user sessions ordered by `updated_at DESC`.
  * **Response (200 OK):** `Array<SessionResponse>`
* **`GET /api/v1/sessions/{session_id}`**
  * **Purpose:** Retrieve session metadata, message history, and associated artifacts.
  * **Response (200 OK):** `SessionDetailResponse`
* **`DELETE /api/v1/sessions/{session_id}`**
  * **Purpose:** Delete session and cascade delete all associated messages and artifacts.
  * **Response (204 No Content)**

### 5.3 Messaging & Real-Time Streaming
* **`POST /api/v1/sessions/{session_id}/messages`**
  * **Purpose:** Post a user query and receive streaming assistant tokens, source citations, and artifact events.
  * **Protocol:** Server-Sent Events (`text/event-stream`).
  * **Request Body:**
    ```json
    {
      "content": "How did Superhuman find product-market fit?",
      "skill_override": null
    }
    ```
  * **SSE Event Types:**
    * `event: token` $\rightarrow$ `data: {"text": "Rahul"}`
    * `event: sources` $\rightarrow$ `data: {"sources": [{"episode_title": "Rahul Vohra on PMF", "guest": "Rahul Vohra", "score": 0.89, "snippet": "..."}]}`
    * `event: artifact_start` $\rightarrow$ `data: {"id": "uuid", "title": "PMF Engine", "type": "html"}`
    * `event: artifact_chunk` $\rightarrow$ `data: {"id": "uuid", "chunk": "<div>...</div>"}`
    * `event: artifact_complete` $\rightarrow$ `data: {"id": "uuid", "version": 1}`
    * `event: done` $\rightarrow$ `data: {"message_id": "uuid", "total_tokens": 420}`
    * `event: error` $\rightarrow$ `data: {"code": "MODEL_TIMEOUT", "message": "The model request timed out."}`

### 5.4 Artifact Management
* **`GET /api/v1/artifacts/{artifact_id}`**
  * **Purpose:** Retrieve a specific artifact's full content and metadata.
  * **Response (200 OK):**
    ```json
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "title": "Interactive PMF Calculator",
      "artifact_type": "html",
      "content": "<!DOCTYPE html><html>...</html>",
      "version": 1,
      "created_at": "2026-09-09T13:16:00Z"
    }
    ```

---

## 6. Request & Response Schemas (Pydantic Strategy)

The backend strictly enforces domain boundaries using Pydantic V2 models. Database ORM models are never directly returned to clients.

```python
# Example Schema Architecture Overview
class SourceCitation(BaseModel):
    chunk_id: UUID
    episode_title: str
    guest_name: str
    timestamp: Optional[str] = None
    relevance_score: float = Field(ge=0.0, le=1.0)
    snippet: str

class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    skill_override: Optional[str] = None

class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    sources: List[SourceCitation] = []
    created_at: datetime

class ArtifactResponse(BaseModel):
    id: UUID
    session_id: UUID
    title: str
    artifact_type: Literal["markdown", "html", "svg"]
    content: str
    version: int
    created_at: datetime
```

---

## 7. Unified Error Model

All error responses from the API conform to a strict, standardized JSON format with unique `request_id` tracking for observability:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Session with id '3fa85f64' does not exist.",
    "request_id": "req-98234-abcd",
    "details": null
  }
}
```

### Standardized Error Codes:
* `INVALID_REQUEST`: Validation failure or malformed JSON payload ($400$).
* `SESSION_NOT_FOUND`: Target session ID does not exist ($404$).
* `ARTIFACT_NOT_FOUND`: Target artifact ID does not exist ($404$).
* `MODEL_UNAVAILABLE`: Configured LLM provider (Ollama / Cloud) is unreachable ($503$).
* `MODEL_TIMEOUT`: Upstream LLM inference exceeded execution deadline ($504$).
* `RETRIEVAL_FAILED`: Database vector search query error ($500$).
* `UNSAFE_ARTIFACT_REJECTED`: Generated code failed security sanitization ($422$).
* `INTERNAL_SERVER_ERROR`: Unhandled exception ($500$).

---

## 8. Configuration Architecture

All application configuration is managed via `pydantic-settings` with type validation, defaults, and hierarchical overrides (`.env` file $\rightarrow$ environment variables).

```python
class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Persistence
    DATABASE_URL: PostgresDsn = "postgresql+asyncpg://postgres:postgres@localhost:5432/lenny_assistant"
    
    # LLM Provider Configuration
    LLM_PROVIDER: Literal["ollama", "cloud", "mock", "fake"] = "mock"
    
    # Local Ollama Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0
    
    # Cloud Provider Settings
    CLOUD_PROVIDER: Literal["anthropic", "openai"] = "anthropic"
    ANTHROPIC_API_KEY: Optional[SecretStr] = None
    OPENAI_API_KEY: Optional[SecretStr] = None
    CLOUD_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Embedding Configuration
    EMBEDDING_PROVIDER: Literal["local", "openai"] = "local"
    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Retrieval Guardrails
    GROUNDING_SIMILARITY_THRESHOLD: float = 0.30
    MAX_RETRIEVAL_CHUNKS: int = 6
```

---

## 9. LLM Provider Abstraction Layer

To ensure zero vendor lock-in and seamless toggling between offline local execution and cloud APIs, all LLM interactions pass through a unified abstract base interface:

```mermaid
classDiagram
    class LLMProvider {
        <<interface>>
        +generate(prompt, system_prompt, options) AsyncIterator[str]
        +generate_structured(prompt, schema, options) Dict
        +check_health() bool
    }

    class OllamaProvider {
        -base_url: str
        -model: str
        -timeout: float
        +generate(prompt, system_prompt, options) AsyncIterator[str]
        +generate_structured(prompt, schema, options) Dict
        +check_health() bool
    }

    class CloudProvider {
        -provider: str
        -api_key: SecretStr
        -model: str
        +generate(prompt, system_prompt, options) AsyncIterator[str]
        +generate_structured(prompt, schema, options) Dict
        +check_health() bool
    }

    LLMProvider <|-- OllamaProvider
    LLMProvider <|-- CloudProvider
```

---

## 10. Agent & Skill Orchestration Architecture

The agent subsystem employs a deterministic routing pipeline designed for speed, low token consumption, and reliable tool execution:

```mermaid
flowchart TD
    UserQuery[User Message / Ship30 API] --> IntentClassifier[Intent Classifier & Router]
    
    IntentClassifier --> |General Product Q&A| QAPath[Grounded Q&A Skill]
    IntentClassifier --> |Request Long-Form Essay| Ship30Path[Ship 30 for 30 Skill]
    IntentClassifier --> |Request Calculator / Template / Widget| ArtifactPath[Artifact Synthesis Skill]

    QAPath --> RetrieveContext[Hybrid Transcript Retrieval]
    Ship30Path --> RetrieveContext
    ArtifactPath --> RetrieveContext

    RetrieveContext --> GuardrailCheck{Max Similarity >= 0.65?}
    
    GuardrailCheck -- No --> RefusalEmitter[Refusal Mode: Explain Corpus Boundaries]
    GuardrailCheck -- Yes --> Synthesizer[LLM Provider Synthesis Engine]

    Synthesizer --> OutputFormatter[Output & Citation Formatter]
    OutputFormatter --> DBCommit[Persist Messages & Sources to PostgreSQL]
```

### 10.1 Ship 30 for 30 Skill Architecture

The `Ship30Skill` ([`backend/app/agent/skills/ship30_skill.py`](file:///d:/AI-ML-assements_2026/lenny-growth-assistant/backend/app/agent/skills/ship30_skill.py)) implements an editorial synthesis pipeline:
1. **Context & Topic Resolution:** Resolves pronouns or conversational follow-up references (e.g., *"turn those ideas into a post"*) by inspecting recent turn history.
2. **Diverse Evidence Gathering:** Retrieves up to 6 high-relevance transcript chunks across multiple podcast episodes via `HybridRetriever`.
3. **Strict Grounding & Refusal Guardrail:** If similarity scores fall below threshold $\tau = 0.65$, returns an explicit refusal rather than hallucinating unsupported essays.
4. **Structured Generation (~1,250 words):** Follows `SYSTEM_PROMPT_SHIP30` with punchy headline, tension hook, 3 grounded pillars with guest attribution, practical implementation, and a 5-step takeaway blueprint.
5. **Traceability:** Returns structured `SourceCitation` objects linking every key claim to the original podcast episode and timestamp.

---

## 11. Knowledge & Retrieval Architecture (RAG)

The knowledge engine transforms raw podcast transcripts into a high-precision, hybrid searchable index:

1. **Ingestion & Metadata Extraction:** Parsers ingest transcript files, extracting speaker labels, episode titles, guest roles, timestamps, and publication dates.
2. **Recursive Semantic Chunking:** Text is split using boundary-aware chunking (target: $500$ tokens, overlap: $100$ tokens), preserving conversational turn boundaries and speaker identity.
3. **Embedding Generation:** Chunks are vectorized using standard embeddings ($1536$-dim for OpenAI or $384$-dim for local SentenceTransformers).
4. **Hybrid Retrieval with Reciprocal Rank Fusion (RRF):**
   $$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
   Combines semantic similarity rank and BM25 keyword rank to ensure both broad conceptual queries and specific name/term queries surface the most relevant source passages.

---

## 12. Artifact Security Architecture

All dynamically generated HTML/CSS/JS artifacts must be treated as untrusted third-party code. The security boundary is enforced at three distinct layers:

```
+-------------------------------------------------------------------------------+
|                             SECURITY LAYER 1: BACKEND                         |
| Server-Side AST & Regex Sanitizer: Strips top/parent references, cookie       |
| access, and unauthorized network endpoints before DB storage.                 |
+-------------------------------------------------------------------------------+
                                      ↓
+-------------------------------------------------------------------------------+
|                             SECURITY LAYER 2: CLIENT                          |
| Client-Side HTML Parsing: Strips inline script mutations attempting           |
| DOM escape before setting iframe source document.                             |
+-------------------------------------------------------------------------------+
                                      ↓
+-------------------------------------------------------------------------------+
|                         SECURITY LAYER 3: BROWSER SANDBOX                     |
| <iframe sandbox="allow-scripts" srcdoc="...">                                 |
| * NO allow-same-origin: Cannot access host cookies, localStorage, or session. |
| * NO allow-top-navigation: Cannot redirect or reload the host application.    |
| * NO allow-popups: Cannot open unmonitored windows.                           |
+-------------------------------------------------------------------------------+
```

---

## 13. Deployment Topology & Networking

The system is packaged as a portable, multi-container Docker Compose application:

```mermaid
flowchart LR
    subgraph Host["Developer Host Machine"]
        Browser["Web Browser (Port 3000)"]
        HostOllama["Local Ollama Daemon (Port 11434)"]
    end

    subgraph DockerNetwork["Docker Bridge Network (lenny-network)"]
        FrontendContainer["frontend (Nginx / Vite) :3000"]
        BackendContainer["backend (FastAPI / Uvicorn) :8000"]
        PostgresContainer["postgres (PostgreSQL 16 + pgvector) :5432"]
        Volume[(pgdata Volume)]
    end

    Browser --> FrontendContainer
    FrontendContainer --> |Proxy /api| BackendContainer
    BackendContainer --> PostgresContainer
    PostgresContainer --> Volume
    BackendContainer -.-> |host.docker.internal:11434| HostOllama
    BackendContainer -.-> |HTTPS /api.anthropic.com| CloudAPI[Anthropic / OpenAI Cloud API]
```

---

## 14. Observability & Telemetry

Every request generates a structured JSON log entry containing:
* `request_id`: Tracing identifier propagated across backend layers.
* `session_id`: Associated conversation session.
* `duration_ms`: Execution time for each lifecycle stage (retrieval, LLM inference, DB commit).
* `tokens`: Prompt tokens, completion tokens, and estimated cost.
* `retrieval_chunks`: Count and top similarity score of retrieved passages.
* `model_provider`: `ollama` or `cloud` (`claude-3-5-sonnet`).

---

## 15. Resilience & Failure Handling

| Failure Scenario | Detection Mechanism | Immediate Fallback Behavior | User Experience |
| :--- | :--- | :--- | :--- |
| **Local Ollama Offline** | Connection refused on `http://localhost:11434` | Return `MODEL_UNAVAILABLE` error event | UI displays descriptive banner: *"Ollama is unreachable. Run `ollama serve` or configure a Cloud API key in settings."* |
| **Cloud API Rate Limited** | HTTP 429 from Anthropic/OpenAI | 3 exponential backoff retries ($1\text{s}, 2\text{s}, 4\text{s}$) | If retries fail, UI displays: *"Cloud model capacity reached. Please retry in a moment."* |
| **Database Disconnection** | SQLAlchemy pool timeout | Async reconnection attempt on next request | UI gracefully notifies of temporary storage delay without crashing the view. |
| **Empty / Low Similarity RAG** | Max similarity score $< 0.65$ | Activate Refusal Skill | Assistant informs user of knowledge boundary with suggested valid queries. |
| **Artifact Script Error** | Window error listener in sandboxed iframe | Capture iframe error event | Artifact Viewer displays non-fatal warning badge with option to view raw code. |

---
*End of System Architecture Document.*

