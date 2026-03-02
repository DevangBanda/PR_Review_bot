# PR Agent Review Bot (Multi-Agent + CI)

A production-minded GitHub Pull Request reviewer bot that listens to **GitHub webhooks**, runs multiple review “agents”
(**Security**, **Performance**, **Style**), and posts a consolidated review comment back to the PR.

- **Webhook server:** FastAPI
- **GitHub integration:** GitHub App (recommended) or PAT fallback
- **Agents:** rule-based + optional LLM augmentation (OpenAI-compatible / Gemini-style via adapter interface)
- **Runs locally:** Docker / docker-compose
- **CI:** GitHub Actions (lint + typecheck + tests)

> ⚠️ This repo ships with **safe, rule-based agents** that work out of the box.  
> If you add an LLM key, the same agents can produce higher-quality feedback.

---

## Features

- ✅ Secure webhook verification (HMAC `X-Hub-Signature-256`)
- ✅ GitHub API client with retries and rate-limit friendly behavior
- ✅ Agent orchestration (parallelizable design)
- ✅ Posts a single **summary review** as a PR comment
- ✅ Idempotency guard to avoid duplicate comments per PR update
- ✅ Structured logging for production debugging

---

## Quickstart (Local)

### 1) Prereqs

- Python 3.11+
- A GitHub App (recommended) **or** a GitHub Personal Access Token (PAT)
- A public webhook endpoint (use `ngrok` for local dev)

### 2) Configure environment

Copy and edit:

```bash
cp .env.example .env
```

### 3) Run

#### Option A: Docker (recommended)

```bash
docker compose up --build
```

The server runs on `http://localhost:8080`.

#### Option B: Local Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## GitHub Webhook Setup

### Recommended: GitHub App

1. Create a GitHub App
2. Enable **Pull requests** events (at minimum):
   - `pull_request` (opened, synchronize, reopened, ready_for_review)
3. Set webhook URL to:
   - `https://<your-public-url>/webhooks/github`
4. Generate and store:
   - App ID
   - Installation ID (per org/repo installation)
   - Private key (PEM)

Set these env vars (see `.env.example`):

- `GITHUB_APP_ID`
- `GITHUB_INSTALLATION_ID`
- `GITHUB_PRIVATE_KEY_PEM`

### PAT fallback (easier, less enterprise)

Set:

- `GITHUB_TOKEN`

---

## What gets reviewed?

The bot fetches:

- PR metadata (title/body)
- Changed files list
- Patch/diff snippets (when available via GitHub API)

Agents apply:

- **Security:** detects obvious secrets, risky patterns, unsafe commands
- **Performance:** common perf pitfalls (N+1 queries hints, heavy loops, sync I/O in async)
- **Style:** basic lint-like observations, naming, formatting (language-agnostic)

If `LLM_PROVIDER` is configured, agents can optionally ask an LLM to generate more nuanced suggestions.

---

## Deploy

Typical deployment options:

- Cloud Run / Render / Fly.io / ECS
- Put the service behind HTTPS (required for GitHub webhooks)
- Set your webhook secret and rotate it periodically

---

## CI

This repository includes a GitHub Actions workflow:

- Ruff (lint)
- Mypy (type check)
- Pytest

---

## Repo structure

```
app/
  main.py
  config.py
  logging.py
  github/
    client.py
    auth.py
    models.py
  agents/
    base.py
    security.py
    performance.py
    style.py
    orchestrator.py
  services/
    reviewer.py
  webhooks/
    github.py
tests/
```

---

## Notes on production readiness

- Use GitHub App credentials (least privilege)
- Consider persistent storage for idempotency if you run multiple replicas
- Add a queue (e.g., Redis/Celery) if you expect high webhook volume

---

## License

MIT
