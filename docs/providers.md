# Model Configuration & Provider Resilience Guide

> **The Lenny Growth Assistant** features a pluggable, bimodal LLM provider abstraction designed for zero-config offline execution via local open-weight models (Ollama) and production cloud API execution (Anthropic Claude, OpenAI).

---

## 1. Supported Providers

| Provider | Provider Setting | Supported Models | Configuration Keys |
| :--- | :--- | :--- | :--- |
| **Ollama (Default)** | `LLM_PROVIDER=ollama` | `llama3.1:8b`, `qwen2.5:7b`, `mistral:7b` | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT_SECONDS` |
| **Anthropic Claude** | `LLM_PROVIDER=cloud`<br>`CLOUD_PROVIDER=anthropic` | `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307` | `ANTHROPIC_API_KEY`, `CLOUD_MODEL`, `CLOUD_TIMEOUT_SECONDS` |
| **OpenAI** | `LLM_PROVIDER=cloud`<br>`CLOUD_PROVIDER=openai` | `gpt-4o`, `gpt-4o-mini` | `OPENAI_API_KEY`, `CLOUD_MODEL`, `CLOUD_TIMEOUT_SECONDS` |
| **Mock / Test** | `LLM_PROVIDER=mock` | Deterministic synthetic mock provider | N/A |

---

## 2. Local Ollama Setup (Default Demo Mode)

For local development and evaluator demos without third-party API keys:

1. **Install and launch Ollama:**
   ```bash
   ollama serve
   ```
2. **Pull the target model:**
   ```bash
   ollama pull llama3.1:8b
   ```
3. **Configure environment:**
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.1:8b
   OLLAMA_TIMEOUT_SECONDS=60.0
   ```
4. **Docker Network note:**
   When running inside Docker Compose on macOS/Windows, set:
   ```env
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   ```

---

## 3. Cloud Provider Setup

To switch to cloud providers:

### Anthropic Claude
```env
LLM_PROVIDER=cloud
CLOUD_PROVIDER=anthropic
CLOUD_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-api03-...
CLOUD_TIMEOUT_SECONDS=45.0
```

### OpenAI
```env
LLM_PROVIDER=cloud
CLOUD_PROVIDER=openai
CLOUD_MODEL=gpt-4o
OPENAI_API_KEY=sk-proj-...
CLOUD_TIMEOUT_SECONDS=45.0
```

---

## 4. Resilience, Guardrails & Failure Modes

The provider layer maps low-level runtime errors into structured HTTP error responses:

| Failure Scenario | HTTP Status | Error Code | Behavior & Actionable Remediation |
| :--- | :---: | :--- | :--- |
| **Ollama daemon unreachable** | `503` | `MODEL_UNAVAILABLE` | Returns clear message: *"Cannot connect to Ollama daemon at http://localhost:11434. Is Ollama running? Run 'ollama serve' or check OLLAMA_BASE_URL."* Session state is preserved. |
| **Inference request timeout** | `504` | `MODEL_TIMEOUT` | Bounded execution aborts after timeout threshold (default: 60s for Ollama, 45s for Cloud). Returns clean 504. |
| **Missing API Key** | `503` | `MODEL_UNAVAILABLE` | Returns *"ANTHROPIC_API_KEY / OPENAI_API_KEY is not configured in environment."* without crashing or leaking secrets. |
| **Invalid Provider Config** | `500` | `CONFIGURATION_ERROR` | Fails fast with clear validation message listing valid options (`ollama`, `cloud`, `mock`). |
| **Unsupported Topic Refusal** | `200` | Refusal Response | When cosine similarity is below `0.65` (no grounded transcript chunks), returns standard polite refusal without hallucination. |

---

## 5. Security & Key Redaction

* Active provider and model names are exposed via `/health` and `/ready` endpoints for operational monitoring.
* API keys are loaded strictly through Pydantic `SecretStr` models.
* No API keys or authorization headers are logged, serialized to JSON, or sent to frontend clients.

