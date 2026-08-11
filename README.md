⚡ Agentless

Autonomous API Debugging & Self-Healing

<p align="center">



</p>

Failure → Investigation → Reproduction → Patch → Verification → Pull Request

Agentless is an AI-powered debugging engine that turns production API failures into verified code changes.

Traditional observability tells a developer what went wrong.

Agentless goes further:

What went wrong → Why it happened → Can we reproduce it → Can we fix it → Does the fix actually work?

🎯 The Core Idea

flowchart LR
    A["🚨 API Failure"] --> B["📥 Ingest"]
    B --> C["🧬 Fingerprint"]
    C --> D["🗺️ Traceback Mapping"]
    D --> E["🧠 Root Cause"]
    E --> F["🧪 Reproduce"]
    F --> G["🩹 Generate Patch"]
    G --> H["🔬 Verify"]
    H --> I["🚀 GitHub PR"]

    style A fill:#ef4444,color:#fff
    style E fill:#7c3aed,color:#fff
    style G fill:#f59e0b,color:#111
    style H fill:#10b981,color:#fff
    style I fill:#24292f,color:#fff

The principle

AI can propose a fix. Execution must prove it.

A generated patch is untrusted until it survives real patch application, reproduction, and regression testing in an isolated workspace.

🚨 The Problem

When an API fails in production, developers often move through a fragmented manual workflow:

Production Failure
       ↓
Read Logs
       ↓
Inspect Stack Trace
       ↓
Find Source Code
       ↓
Understand Root Cause
       ↓
Reproduce Failure
       ↓
Write Fix
       ↓
Run Tests
       ↓
Create Pull Request

The problem is not only discovering the error.

The expensive part is everything after the error is discovered.

Existing observability answers:

"What happened?"

Agentless aims to answer:

"Can we investigate, reproduce, verify and prepare the fix?"

💡 What Agentless Does

Stage

What happens

📥 Ingest

Receives structured API failure information

🧬 Fingerprint

Groups duplicate incidents using stable fingerprints

🛡️ Scrub

Removes sensitive request information

🗺️ Map

Connects traceback frames to repository source

🧠 Investigate

Generates structured root-cause hypotheses

🧪 Reproduce

Creates a test reproducing the failure

🩹 Patch

Generates a candidate code change

🔬 Verify

Applies the patch and executes tests

🚀 Ship

Creates a GitHub branch, commit and Pull Request

🧠 Why "Agentless"?

Agentless is deliberately built around a deterministic execution pipeline.

AI is used where reasoning matters:

Reason → Generate → Explain

The execution layer remains deterministic:

Clone → Apply → Test → Validate

This separation gives the system a clear safety boundary:

The model can suggest. The verification engine decides whether the suggestion survives execution.

🏗️ Architecture

flowchart TB
    UI["🖥️ Next.js Dashboard"]

    API["⚡ FastAPI Backend"]

    ING["📥 Ingestion & Fingerprinting"]
    MAP["🗺️ Traceback / Source Mapping"]
    AI["🧠 LLM Analysis"]
    REP["🧪 Reproduction"]
    PATCH["🩹 Patch Generation"]
    VERIFY["🔬 Verification Engine"]
    GH["🐙 GitHub Integration"]

    SANDBOX["📦 Isolated Workspace / Sandbox"]
    DB["🗄️ Incident Database"]

    UI --> API
    API --> ING
    ING --> DB
    ING --> MAP
    MAP --> AI
    AI --> REP
    REP --> SANDBOX
    AI --> PATCH
    PATCH --> VERIFY
    VERIFY --> SANDBOX
    VERIFY --> GH
    GH --> UI

✨ Key Features

01 · 📥 Agentless Failure Ingestion

Applications can submit structured failure information through the backend API.

POST /logs

No heavy proprietary instrumentation layer is required for the core workflow.

02 · 🧬 Stable Incident Fingerprinting

Failures are converted into stable SHA-256 fingerprints using incident characteristics such as:

Route

Error class

Error message

Stack frames

Source context

This allows repeated occurrences of the same failure to be grouped together.

03 · 🛡️ Sensitive Data Scrubbing

Incoming request information is sanitized before being displayed or processed.

Examples include:

Authorization
API keys
Cookies
Session headers

Sensitive values are replaced with:

[FILTERED]

04 · 🗺️ Traceback → Source Mapping

Stack-trace frames are mapped back to relevant repository files.

Instead of asking the model to reason from only:

ValueError: something failed

the investigation layer can receive:

Error
  ↓
Traceback frame
  ↓
Source file
  ↓
Relevant source context

05 · 🧠 AI Root-Cause Investigation

The LLM investigation layer can reason over:

Incident details

Traceback frames

Relevant source code

Repository context

and produce structured hypotheses instead of an unstructured chat response.

06 · 🧪 Automated Failure Reproduction

Agentless generates a reproducer intended to demonstrate the original failure.

The reproducer is executed inside an isolated verification environment rather than directly against the developer's working tree.

07 · 🩹 AI Patch Generation

Once a hypothesis is selected, the patch layer generates a candidate code change.

The patch is treated as untrusted output until the verification engine accepts it.

08 · 🔬 Verification-First Safety Gate

The candidate patch goes through a real execution loop:

Generated Patch
      ↓
git apply --check
      ↓
Apply Patch
      ↓
Run Reproducer
      ↓
Run Existing Tests
      ↓
PASS ───────────────→ Eligible for PR
  │
  └── FAIL ─────────→ Reject / Investigate Again

This is the heart of Agentless.

09 · 🚀 GitHub Automation

After verification succeeds, the system can:

Create a fix branch

Commit the verified change

Push the branch

Create a Pull Request

The final merge remains under developer control.

🔬 Verification in the Demo

The implemented end-to-end verification flow has been exercised on the sample API failure:

POST /orders
quantity = -1
        ↓
ValueError
        ↓
Traceback mapped to source
        ↓
Candidate patch generated
        ↓
git apply --check       ✅
Patch application       ✅
Reproducer test         ✅
Regression suite        ✅
Original failure fixed  ✅
Fix branch pushed       ✅
GitHub Pull Request     ✅

Example verified behavior

Before:

quantity = -1
        ↓
HTTP 500

After the verified patch:

quantity = -1
        ↓
HTTP 400

The resulting change was pushed through the real GitHub integration and a Pull Request was created.

🧪 Testing

The backend test suite currently contains:

63 tests

Run:

cd backend
.venv\Scripts\pytest -q

Frontend production build:

cd frontend
npm run build

Convenience scripts are available under:

scripts/
├── run-tests.ps1
└── start-dev.ps1

🛠️ Tech Stack

Layer

Technology

Purpose

🖥️ Frontend

Next.js + TypeScript

Investigation dashboard

⚡ Backend

FastAPI

API and orchestration

🐍 Core

Python

Analysis and automation

🧠 AI

OpenAI-compatible provider

Hypotheses, reproduction and patches

🐙 Git

Git + GitHub API

Repository and PR automation

🔬 Verification

Git + Pytest

Patch and regression validation

📦 Isolation

Sandbox / Docker execution

Safer verification

🗄️ Persistence

SQLAlchemy / SQLite-compatible setup

Incident storage

📁 Project Structure

agentless/
│
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   │       ├── analysis/
│   │       ├── github/
│   │       ├── ingestion/
│   │       ├── patch/
│   │       ├── reproduction/
│   │       └── verification/
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
│   └── package.json
│
├── sandbox/
│   └── sample_repo/
│
├── scripts/
├── docs/
├── .env.example
├── .gitignore
└── README.md

🚀 Run Locally

Prerequisites

Python 3.10+

Node.js 18+

npm

Git

Docker Desktop for sandboxed verification

GitHub token for repository operations

LLM API key for live AI mode

1. Configure environment

Copy-Item .env.example .env

For deterministic demonstration mode:

LLM_PROVIDER=mock

For live LLM mode:

LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key

Also configure the GitHub token and database settings required by the project.

2. Start backend

cd backend

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

python -m uvicorn app.main:app --port 8000

Backend:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

3. Start frontend

Open another terminal:

cd frontend
npm install
npm run dev

Dashboard:

http://localhost:3000

🎬 Demo Flow

For the PEC Hacks demonstration, the project can be presented as a single failure moving through the complete lifecycle:

                    🚨
              API FAILURE
                    │
                    ▼
             📥 INGESTION
                    │
                    ▼
             🧬 INCIDENT
              FINGERPRINT
                    │
                    ▼
             🗺️ SOURCE MAP
                    │
                    ▼
             🧠 AI ANALYSIS
                    │
                    ▼
             🧪 REPRODUCER
                    │
                    ▼
              🩹 PATCH
                    │
                    ▼
             🔬 VERIFICATION
                    │
              ┌─────┴─────┐
              │           │
            FAIL         PASS
              │           │
              ▼           ▼
          REJECT       🚀 PR

The important demo moment

The system does not say:

"The AI generated a patch, therefore the bug is fixed."

It says:

"The generated patch was applied, the failure was reproduced, the regression suite passed, and only then was the change prepared for GitHub."

🔐 Security & Safety

Agentless includes several safeguards around automated debugging:

🛡️ Sensitive data scrubbing

Request information is sanitized before processing.

📦 Isolated execution

Generated reproducer and patch verification are performed in a dedicated workspace/sandbox.

🧹 Clean workspace verification

The patch is tested against a clean repository state rather than relying on the developer's local working tree.

👨‍💻 Human-controlled merge

Agentless prepares the Pull Request; developers retain final control over merging.

🧩 Provider Modes

Agentless supports a deterministic mock provider for demonstrations and tests, while the architecture also supports a real OpenAI provider.

🎭 Mock Provider

Useful for:

Hackathon demonstrations

Deterministic tests

Offline development

Environments without API credits

LLM_PROVIDER=mock

🧠 Live Provider

For real LLM-powered investigation:

LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key

The live provider requires an API key with available quota.

Submission note: the demonstrated sample workflow uses the deterministic mock provider for reproducibility. The verification, sandbox, Git and GitHub portions of the pipeline remain real.

🏆 Why Agentless Is Different

Traditional Observability

Agentless

📊 Shows failures

🔧 Investigates failures

🔍 Shows traces

🗺️ Maps traces to source

👨‍💻 Developer reproduces manually

🧪 Generates a reproducer

✍️ Developer writes the patch

🩹 Generates a candidate patch

🧑‍💻 Developer validates manually

🔬 Executes verification

📋 Developer opens PR

🚀 Automates verified PR preparation

The differentiator

Agentless closes the loop between observability and remediation — with execution-based verification as the safety gate.

📊 Current Implementation

Component

Status

API failure ingestion

✅

Incident fingerprinting

✅

Sensitive-data scrubbing

✅

Traceback parsing

✅

Source mapping

✅

Hypothesis pipeline

✅

Reproduction pipeline

✅

Patch generation

✅

git apply verification

✅

Regression testing

✅

GitHub branch / commit / push

✅

Pull Request creation

✅

Next.js dashboard

✅

Mock provider

✅

Real OpenAI provider

✅*

* Requires a funded API key with available quota.

🔗 Repository

github.com/NITISH-027/agentless-api-observability

Explore the code → inspect the architecture → run the demo

👥 Team VULCAN

Panimalar Engineering College · Chennai

Member

Role

Institution

City

Nitish P

AI & Backend Engineer

Panimalar Engineering College

Chennai

Niranjan B

Systems & Integration

Panimalar Engineering College

Chennai

Neal Patrick A

Frontend Engineer

Panimalar Engineering College

Chennai

<p align="center">

⚡ Agentless

From production failure to verified Pull Request.

Built for PEC Hacks 4.0 by Team VULCAN.

</p>
