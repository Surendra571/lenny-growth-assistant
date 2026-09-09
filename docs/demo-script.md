# The Lenny Growth Assistant — 2-to-3 Minute Demo Walkthrough Script

> **Purpose:** Step-by-step presentation guide for demonstrating **The Lenny Growth Assistant** in a 2–3 minute video presentation.

---

## Demo Overview & Timing

| Timestamp | Phase | Action / Screen Focus | Key Talking Points |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:20** | **Introduction & Architecture** | Full-screen app view (`http://localhost:3000`) | *"This is The Lenny Growth Assistant, a full-stack, enterprise-grade AI assistant designed to extract actionable product and growth advice from Lenny's Podcast transcripts with verifiable citations, Ship 30 for 30 essay generation, and sandboxed interactive artifact rendering."* |
| **0:20 – 0:50** | **Grounded Q&A Demo** | Click *"Rahul Vohra on PMF"* prompt or type query | Point out the answer grounded on Superhuman's 40% disappointed metric. Expand the **Verified Podcast Sources** drawer to highlight episode title, guest name, timestamp, and relevance score. |
| **0:50 – 1:20** | **Contextual Follow-Up** | Ask: *"How does this compare with Elena Verna's B2B growth loops?"* | Explain multi-turn memory and how the hybrid vector + lexical retriever synthesizes cross-episode insights without hallucinating. |
| **1:20 – 1:55** | **Ship 30 for 30 Synthesis** | Type: *"Turn that into a Ship 30 for 30 article."* | Point out automatic intent classification and skill dispatch. Show the structured ~1,250-word essay with a compelling hook, 3 core pillars, and practical takeaway checklist. |
| **1:55 – 2:25** | **Artifact Studio & Security** | Click **[Open Artifact]** button in the chat | Showcase the side-by-side Artifact Studio pane. Toggle between **Rendered Preview** and **Source Code**. Highlight the triple-layer security model (`sandbox="allow-scripts"` without `allow-same-origin`, server-side AST sanitizer, and strict CSP). |
| **2:25 – 2:45** | **Provider Resilience & Wrap-up** | Top Header badge & `/health` / `/ready` | Show the active provider indicator (`Ollama · llama3.1:8b` or `Cloud:Anthropic`). Emphasize session boundary isolation and offline local execution readiness. |

---

## Exact Script & Prompts

### Step 1: Initial Question (Grounded Q&A)
* **Prompt:**
  ```text
  How did Rahul Vohra measure product-market fit for Superhuman using the 40% rule?
  ```
* **Key Visuals to Show:**
  * Grounded answer detailing the Sean Ellis question and segment isolation.
  * Verified podcast sources drawer (Episode: *Superhuman's Product-Market Fit Engine*, Guest: *Rahul Vohra*).

### Step 2: Contextual Follow-Up
* **Prompt:**
  ```text
  How would an early-stage B2B founder apply those ideas alongside self-serve PLG flywheels?
  ```
* **Key Visuals to Show:**
  * Multi-turn session context preservation connecting PMF metrics with Elena Verna's PLG loops.

### Step 3: Demonstrating Knowledge Boundary Guardrails (Anti-Hallucination)
* **Prompt:**
  ```text
  How do I bake chocolate chip cookies from scratch?
  ```
* **Key Visuals to Show:**
  * Instant, deterministic Knowledge Boundary Refusal (`STANDARD_REFUSAL_MESSAGE`).
  * Emphasize: Zero LLM tokens consumed, zero hallucinations, zero fabricated podcast citations.

### Step 4: Ship 30 for 30 Article Generation
* **Prompt:**
  ```text
  Turn that into a Ship 30 for 30 article.
  ```
* **Key Visuals to Show:**
  * Editorial card in chat showing title, word count (~1,250 words), and 3 grounded pillars.
  * Click **[Open Artifact]** to view the auto-persisted Markdown artifact in the Artifact Studio pane.

---

## Resilience & Fallback Plan

* **If Ollama is not running locally:**
  * The top header indicates provider status. If an inference request is sent while the daemon is offline, the UI displays a clean, user-friendly 503 error banner: *"Cannot connect to Ollama daemon at http://localhost:11434. Is Ollama running? Run 'ollama serve'."*
  * Start Ollama in a separate terminal: `ollama serve`, then click **Retry** in the app to demonstrate clean recovery.
* **If running in Cloud Mode:**
  * Ensure `LLM_PROVIDER=cloud`, `CLOUD_PROVIDER=anthropic`, and `ANTHROPIC_API_KEY=sk-ant-...` are configured in `.env`.
* **If presenting offline / without internet:**
  * The entire application runs 100% locally with Docker Compose, local PostgreSQL + `pgvector`, local embedding models, and local Ollama (`llama3.1:8b`).

