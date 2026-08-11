# ⚡ Agentless

### Autonomous API Debugging & Self-Healing

[![PEC Hacks 4.0](https://img.shields.io/badge/PEC%20Hacks-4.0-7C3AED?style=for-the-badge)](https://github.com/NITISH-027/agentless-api-observability)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-Dashboard-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![GitHub](https://img.shields.io/badge/GitHub-Automation-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/NITISH-027/agentless-api-observability)

> **Failure → Investigation → Reproduction → Patch → Verification → Pull Request**

Agentless is an AI-powered, agentless debugging engine that turns production API failures into **verified code changes**.

Instead of stopping at observability and showing developers a stack trace, Agentless follows the failure through the complete debugging lifecycle:

1. Ingest the API failure
2. Fingerprint and deduplicate the incident
3. Map the traceback to source code
4. Generate root-cause hypotheses
5. Reproduce the failure in an isolated environment
6. Generate a candidate code patch
7. Apply and verify the patch
8. Run regression tests
9. Create a GitHub Pull Request for developer review

The key principle is simple:

> **AI can propose a fix. Execution must prove it.**

### ⚙️ At a Glance

| 🔍 **Investigate** | 🧪 **Reproduce** | 🛠️ **Repair** | ✅ **Verify** | 🔗 **Ship** |
|---|---|---|---|---|
| Traceback → source | Isolated sandbox | AI-generated patch | Tests + `git apply` | GitHub PR |

---

## 🚨 The Problem

Modern APIs fail in production every day.

When a failure occurs, developers typically have to:

```text
Production Error
      ↓
Inspect Logs
      ↓
Read Stack Trace
      ↓
Find Source Code
      ↓
Understand Root Cause
      ↓
Reproduce Bug
      ↓
Write Fix
      ↓
Run Tests
      ↓
Create Pull Request

This process is manual, fragmented and time-consuming.

Most observability tools are excellent at answering:

"What went wrong?"

But they generally stop there.

Agentless focuses on the next question:

"Can we investigate, reproduce, verify and prepare the fix automatically?"

💡 Our Solution

Agentless provides a closed-loop debugging workflow:



                    ┌──────────────────┐
                    │   API FAILURE    │
                    └────────┬─────────┘
                             ↓
                  ┌─────────────────────┐
                  │ Ingest & Fingerprint│
                  └─────────┬───────────┘
                            ↓
                  ┌─────────────────────┐
                  │ Traceback Mapping   │
                  └─────────┬───────────┘
                            ↓
                  ┌─────────────────────┐
                  │ Root Cause Analysis │
                  │    AI Hypotheses    │
                  └─────────┬───────────┘
                            ↓
                  ┌─────────────────────┐
                  │ Failure Reproduction│
                  │   Isolated Sandbox  │
                  └─────────┬───────────┘
                            ↓
                  ┌─────────────────────┐
                  │   Patch Generation  │
                  └─────────┬───────────┘
                            ↓
                  ┌─────────────────────┐
                  │ Patch Verification  │
                  │ git apply + tests   │
                  └─────────┬───────────┘
                            ↓
                     ┌──────────────┐
                     │ GitHub Pull  │
                     │   Request    │
                     └──────────────┘

Verification is the safety gate.

Agentless does not blindly commit an AI-generated change.

A patch must successfully pass:

git apply --check

Patch application

Generated reproducer test

Existing regression test suite

Only after verification does the system proceed toward a Pull Request.

✨ Key Features

📥 01 — Agentless Failure Ingestion

Applications can send structured failure information directly to:



POST /logs

No proprietary SDK or heavy instrumentation layer is required.

🧬 02 — Stable Incident Fingerprinting

Failures are converted into stable SHA-256 fingerprints using characteristics such as:

Route

Error class

Error message

Stack frames

Source context

This allows repeated occurrences of the same failure to be grouped together.

🛡️ 03 — Sensitive Data Scrubbing

Incoming request information is sanitized before being displayed or processed.

Sensitive values such as:

Authorization tokens

API keys

Cookies

Session headers

are filtered to:



[FILTERED]

🗺️ 04 — Traceback → Source Mapping

The system analyzes stack traces and maps execution frames back to relevant repository source files.

This provides the AI investigation layer with actual source context instead of relying only on the error message.

🧠 05 — AI Root-Cause Investigation

The LLM layer can analyze:

Incident details

Traceback frames

Relevant source code

Repository context

and produce structured root-cause hypotheses.

🧪 06 — Automated Failure Reproduction

Agentless generates a reproducer intended to demonstrate the original failure.

The reproducer is executed in an isolated verification environment rather than against the original repository.

🩹 07 — AI Patch Generation

Once a root cause has been identified, the system generates a candidate code patch.

The generated patch is treated as untrusted until verified.

🔬 08 — Isolated Patch Verification

The candidate patch is applied inside a clean workspace.

The verification pipeline checks:



Patch
 ↓
git apply --check
 ↓
Apply Patch
 ↓
Run Reproducer
 ↓
Run Existing Tests
 ↓
PASS / FAIL

🚀 09 — GitHub Automation

When verification succeeds, Agentless can:

Create a fix branch

Commit the verified change

Push the branch

Open a Pull Request

Developers remain in control of the final merge.

🧠 Why "Agentless"?

Agentless is intentionally designed around a deterministic backend pipeline rather than requiring a continuously running autonomous coding agent.

The AI is used where reasoning is valuable:



Reason → Generate → Verify

The execution environment remains deterministic:



Clone → Apply → Test → Validate

This separation makes the system easier to inspect, reproduce and trust.

🏗️ Architecture



┌─────────────────────────────────────────────────────┐
│                    FRONTEND                         │
│              Next.js Dashboard                     │
│                                                     │
│ Incidents │ Investigations │ Repositories │ PRs    │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                    FASTAPI                          │
│                  Backend API                        │
├─────────────────────────────────────────────────────┤
│ Ingestion │ Analysis │ Reproduction │ Verification │
│           │          │              │               │
│           │          │              │               │
│           └──────────┴──────────────┘               │
│                       │                             │
│                  LLM Provider                      │
│              OpenAI / Mock Provider                │
└───────────┬───────────────────────┬─────────────────┘
            │                       │
            ▼                       ▼
   ┌─────────────────┐      ┌──────────────────┐
   │ GitHub Services │      │ Sandbox / Docker │
   │                 │      │                  │
   │ Clone           │      │ Reproduce        │
   │ Branch          │      │ Apply Patch      │
   │ Commit          │      │ Run Tests        │
   │ Push            │      │ Verify           │
   │ Pull Request    │      │                  │
   └─────────────────┘      └──────────────────┘

🛠️ Tech Stack

LayerTechnologyPurpose





Frontend

Next.js + TypeScript

Incident investigation dashboard

Backend

FastAPI

Core API and orchestration

Language

Python

Analysis, verification and automation

AI

OpenAI-compatible LLM

Hypotheses, reproduction and patch generation

GitHub

GitHub API

Repository, branch and PR automation

Verification

Git / Pytest

Patch and regression validation

Isolation

Docker / Python Sandbox

Safe execution environment

Database

SQLAlchemy / SQLite-compatible configuration

Incident persistence

📁 Project Structure



agentless/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── health.py
│   │   │       ├── logs.py
│   │   │       └── github_routes.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── logging.py
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   │
│   │   └── services/
│   │       ├── analysis/
│   │       ├── github/
│   │       ├── ingestion/
│   │       ├── patch/
│   │       ├── patching/
│   │       ├── reproduction/
│   │       ├── verification/
│   │       └── pull_requests/
│   │
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── incidents/
│   │   ├── investigations/
│   │   ├── repositories/
│   │   ├── pull-requests/
│   │   └── settings/
│   ├── public/
│   ├── types/
│   └── package.json
│
├── sandbox/
│   └── sample_repo/
│
├── scripts/
│   ├── e2e-audit.py
│   ├── run-tests.ps1
│   └── start-dev.ps1
│
├── docs/
│   └── architecture.md
│
├── .env.example
├── .gitignore
└── README.md

🚀 Running Locally

Prerequisites

Python 3.10+

Node.js 18+

npm

Git

Docker Desktop (required for sandboxed verification)

GitHub token for repository operations

LLM API key for live AI mode

1. Configure Environment

Copy the example environment file:



Copy-Item .env.example .env

Configure the required values:



GITHUB_TOKEN=your_github_token
LLM_PROVIDER=mock
LLM_API_KEY=your_llm_key
DATABASE_URL=your_database_url
SANDBOX_IMAGE=python:3.10-slim

Demo Mode

For deterministic demonstrations:



LLM_PROVIDER=mock

The mock provider is intentionally retained for:

Offline demonstrations

Deterministic testing

CI environments

Environments without LLM API credits

Live AI Mode

For live LLM-powered investigation:



LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key

▶️ Start the Backend



cd backend

python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt

python -m uvicorn app.main:app --port 8000

Backend:



http://127.0.0.1:8000

Swagger API documentation:



http://127.0.0.1:8000/docs

▶️ Start the Frontend

Open another terminal:



cd frontend

npm install

npm run dev

Dashboard:



http://localhost:3000

🧪 Testing

Run the backend test suite:



cd backend

.venv\Scripts\pytest -q

The current project test suite contains:



63 tests

Frontend production build:



cd frontend

npm run build

Convenience scripts are also available:



powershell .\scripts\run-tests.ps1

and:



powershell .\scripts\start-dev.ps1

🔬 Verification-First Pipeline

The most important engineering property of Agentless is that AI-generated code is not automatically trusted.

A generated patch passes through:



AI Generated Patch
        │
        ▼
┌─────────────────┐
│ git apply check │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Apply to Clean  │
│ Verification WS │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Run Reproducer  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Run Test Suite  │
└────────┬────────┘
         │
      PASS?
      /    \
    YES     NO
     │       │
     ▼       ▼
Create PR   Reject

This creates an important boundary:

No verified patch → No Pull Request

🎯 Example Failure

Consider an API receiving:



{
  "quantity": -1
}

The application raises:



ValueError:
Invalid quantity: quantity cannot be negative

Agentless can transform the debugging process into:



Incident
   ↓
Traceback
   ↓
Relevant Source Code
   ↓
Root Cause Hypothesis
   ↓
Failure Reproducer
   ↓
Candidate Patch
   ↓
git apply
   ↓
Regression Tests
   ↓
Verified Fix
   ↓
GitHub Pull Request

Instead of giving the developer another stack trace, the system prepares a reviewable, verified change.

🔐 Security Considerations

Agentless is designed with several safety boundaries:

Sensitive data scrubbing

Incoming sensitive headers and credentials are filtered before being exposed in the dashboard.

Isolated execution

Generated code and tests are executed in a dedicated verification environment rather than directly against the developer's working repository.

Clean workspace verification

Patches are verified against a clean repository workspace.

Human-controlled merge

Agentless creates a Pull Request rather than silently merging changes into the production branch.

📊 Current Implementation Status

CapabilityStatus



API failure ingestion

✅

Incident fingerprinting

✅

Sensitive data scrubbing

✅

Traceback parsing

✅

Source-code mapping

✅

Hypothesis pipeline

✅

Reproducer pipeline

✅

Patch generation

✅

Git patch validation

✅

Sandbox verification

✅

Regression testing

✅

GitHub branch creation

✅

GitHub push

✅

Pull Request automation

✅

Mock LLM provider

✅

Live OpenAI provider

✅

Frontend dashboard

✅

🧩 Demo / Provider Note

Agentless supports two LLM modes:

Mock Provider

The deterministic provider is used for reproducible demonstrations and automated tests.

It allows the complete pipeline to be demonstrated without depending on external model availability or API quota.

OpenAI Provider

The architecture also supports the real OpenAI provider for live hypothesis, reproducer and patch generation when a valid API key with available quota is configured.

The provider abstraction allows the verification pipeline to remain independent of the selected LLM provider.

🏆 What Makes Agentless Different?

Traditional observability:



Detect → Alert → Developer investigates

AI coding assistants:



Developer asks → AI suggests code

Agentless:



Failure
   ↓
Investigate
   ↓
Reproduce
   ↓
Generate Fix
   ↓
Execute Fix
   ↓
Verify Fix
   ↓
Create PR

The difference is the verification loop.

Agentless is designed around the idea that:

A fix is not a fix until the system can reproduce the failure and prove that the proposed change resolves it without breaking the existing test suite.

🔗 Repository

NITISH-027/agentless-api-observability

⭐ Explore the code • Run the dashboard • Inspect the architecture

👥 Team VULCAN

Panimalar Engineering College — Chennai

MemberRole



Nitish P

AI & Backend Engineer

Niranjan B

Systems & Integration

Neal Patrick A

Frontend Engineer
