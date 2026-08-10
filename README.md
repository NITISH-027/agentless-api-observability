# Agentless API Observability & Automated Debugging Platform

A lightweight, agentless platform that ingests structured API failure logs, matches and deduplicates failures using stable characteristics, automatically reproduces issues in docker-isolated sandboxes, and verifies/patches the code before submitting GitHub Pull Requests.

---

## Key Features

1. **Agentless Ingestion**: Simply send JSON payloads of your app exceptions directly to our REST API endpoint (`POST /logs`). No proprietary SDK or heavy middleware required.
2. **Stable Hashed Fingerprinting**: Generates stable SHA-256 signatures of exceptions using routes, error classes, messages, and stack frame contexts to automatically aggregate duplicates.
3. **Sensitive Data Scrubbing**: Automatically filters authorization tokens, API keys, cookies, and session headers to `[FILTERED]`.
4. **Interactive Dashboard**: Modern, clean TypeScript dashboard to list and drill down on incidents, view sanitized headers, query info, and trace logs.

---

## Directory Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI Application Startup
│   ├── api/
│   │   └── routes/
│   │       ├── health.py        # /health Endpoint
│   │       └── logs.py          # /logs, /incidents Endpoints
│   ├── core/
│   │   ├── config.py            # Pydantic Settings Validation
│   │   ├── database.py          # SQLAlchemy Session Management
│   │   └── logging.py           # Logging Setup Configuration
│   ├── models/                  # SQLAlchemy DB Entities (Incident)
│   ├── schemas/                 # Pydantic Ingestion Request Payloads
│   └── services/                # Extensible Business Logic Services
│       ├── github/
│       ├── ingestion/           # Scrubbers & Fingerprinting
│       ├── analysis/
│       ├── reproduction/
│       ├── verification/
│       ├── patching/
│       └── pull_requests/
└── tests/                       # Pytest Integration Suite

frontend/
├── app/                         # Next.js App Router (Layouts & Pages)
├── components/                  # Shared UI components
├── lib/                         # apiClient Abstractions
└── types/                       # TypeScript Interface Definitions

sandbox/                         # Isolation scripts & Docker configurations
docs/                            # High-level architecture documentation
scripts/                         # Developer build & verify script tools
```

---

## Environment Variables

Copy `.env.example` into a new `.env` file at the root:

```bash
cp .env.example .env
```

| Variable Name | Description | Example Value |
| :--- | :--- | :--- |
| `GITHUB_TOKEN` | GitHub Personal Access Token for Repo cloning/read | `ghp_abcd1234...` |
| `GITHUB_APP_ID` | GitHub App Integration ID | `12345` |
| `GITHUB_PRIVATE_KEY` | Private RSA key for GitHub Integration auth | `-----BEGIN RSA PRIVATE KEY-----...` |
| `LLM_PROVIDER` | Targeted Model Provider (openai/anthropic/gemini) | `openai` |
| `LLM_API_KEY` | LLM Provider access token secret | `sk-proj-...` |
| `DATABASE_URL` | Supabase or PostgreSQL Connection String | `postgresql://user:pass@localhost:5432/db` |
| `SANDBOX_IMAGE` | Execution Docker Sandbox Container Image | `python:3.10-slim` |

---

## Local Development Setup

### Prerequisite Checklist
* **Python 3.10+** (tested up to Python 3.14)
* **Node.js 18+** & **npm**

### 1. Initialize Python Backend
Navigate to the backend, build the virtual environment, install requirements, and start the development server:

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# or: source .venv/bin/activate (Linux/macOS)

pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend server is accessible at `http://127.0.0.1:8000`. You can inspect the Swagger docs at `http://127.0.0.1:8000/docs`.

### 2. Initialize Frontend NextJS Dashboard
Navigate to the frontend directory, install npm packages, and spin up the next dev server:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` to access the dashboard.

---

## Testing & Verifications

Run the automated backend test suite using:

```bash
cd backend
.venv\Scripts\pytest
```

Build the frontend for production to check TypeScript compile checks:

```bash
cd frontend
npm run build
```

Alternatively, use the convenience scripts:
- `powershell .\scripts\start-dev.ps1` to spin up both servers at once.
- `powershell .\scripts\run-tests.ps1` to execute all tests and builds in one go.
