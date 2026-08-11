<div align="center">

⚡ AGENTLESS

Autonomous API Debugging & Self-Healing

From production failure → verified fix → GitHub Pull Request

<br>

<a href="https://github.com/NITISH-027/agentless-api-observability">
  <img src="https://img.shields.io/badge/PEC%20HACKS-4.0-7C3AED?style=for-the-badge&labelColor=111827" alt="PEC Hacks 4.0">
</a>
<a href="https://github.com/NITISH-027/agentless-api-observability">
  <img src="https://img.shields.io/badge/STATUS-MVP%20READY-10B981?style=for-the-badge&labelColor=111827" alt="MVP Ready">
</a>
<a href="https://github.com/NITISH-027/agentless-api-observability">
  <img src="https://img.shields.io/badge/AI-POWERED-8B5CF6?style=for-the-badge&labelColor=111827" alt="AI Powered">
</a>

<br><br>

Observability tells you that an API failed.Agentless investigates why, reproduces the failure, verifies a fix, and prepares the PR.

<br>

🚀 Explore Repository ·📖 Architecture ·🐛 Report Issue

</div>

🧨 The Problem

Production API failures usually create a long chain of manual work.

┌─────────────────┐
│  🚨 API FAILURE │
└────────┬────────┘
         ↓
   📋 Inspect Logs
         ↓
   🔎 Read Traceback
         ↓
   🗺️ Find Source
         ↓
   🧠 Understand Cause
         ↓
   🧪 Reproduce Bug
         ↓
   ✍️ Write Fix
         ↓
   🧪 Run Tests
         ↓
   🌿 Create Branch
         ↓
   🔗 Open PR

The hidden cost

Developers don't just spend time finding the error.

They spend time connecting:

logs → source → root cause → reproduction → code change → validation → collaboration

Most observability platforms stop around the first half.

⚡ The Agentless Difference

<div align="center">

FAILURE → INVESTIGATION → REPRODUCTION → PATCH → VERIFICATION → PR

</div>

Agentless turns the debugging lifecycle into one connected workflow.

<table>
<tr>
<td width="50%" valign="top">

🔍 Traditional Observability

📊 Detects failures

📝 Displays logs

🧵 Shows stack traces

📈 Provides dashboards

👨‍💻 Developer takes over

Output:

"Something went wrong."

</td>

<td width="50%" valign="top">

⚡ Agentless

📥 Ingests the failure

🧬 Fingerprints the incident

🗺️ Maps traceback to source

🧠 Generates root-cause hypotheses

🧪 Generates reproduction

🩹 Generates candidate patch

🔬 Executes verification

🚀 Prepares GitHub PR

Output:

"Here is the verified fix."

</td>
</tr>
</table>

🧠 How It Works

flowchart LR
    A["🚨<br/>API Failure"]
    B["📥<br/>Ingest"]
    C["🧬<br/>Fingerprint"]
    D["🗺️<br/>Traceback<br/>Mapping"]
    E["🧠<br/>AI Root Cause"]
    F["🧪<br/>Reproduce"]
    G["🩹<br/>Patch"]
    H["🔬<br/>Verify"]
    I["🚀<br/>GitHub PR"]

    A --> B --> C --> D --> E --> F --> G --> H --> I

    style A fill:#DC2626,color:#fff,stroke:#7F1D1D
    style E fill:#7C3AED,color:#fff,stroke:#4C1D95
    style G fill:#F59E0B,color:#111,stroke:#92400E
    style H fill:#10B981,color:#fff,stroke:#065F46
    style I fill:#111827,color:#fff,stroke:#374151

🔥 The Core Innovation

Verification-First AI Debugging

The most important design decision in Agentless is simple:

AI-generated code is never trusted just because the model generated it.

The patch must survive an execution-based safety gate.

                 🧠 AI
                  │
                  ▼
           ┌──────────────┐
           │ Candidate Fix│
           └──────┬───────┘
                  │
                  ▼
        ┌───────────────────┐
        │ git apply --check │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ Apply Patch       │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ Run Reproducer    │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ Run Regression    │
        │ Test Suite        │
        └─────────┬─────────┘
                  │
          ┌───────┴───────┐
          ▼               ▼
       ❌ FAIL          ✅ PASS
          │               │
          ▼               ▼
       Reject          🚀 PR

The rule

AI proposes. Execution proves.

🧩 What Happens Inside the Pipeline?

<details>
<summary><b>01 · 📥 Failure Ingestion</b></summary>

Agentless receives structured API failure information and creates an incident record.

The system captures the information required for downstream investigation without forcing the developer to manually reconstruct the failure.

</details>

<details>
<summary><b>02 · 🧬 Incident Fingerprinting</b></summary>

Repeated failures are converted into stable fingerprints using incident characteristics such as:

route

error class

error message

stack frames

source context

This prevents the same underlying problem from becoming a collection of disconnected incidents.

</details>

<details>
<summary><b>03 · 🛡️ Sensitive Data Scrubbing</b></summary>

Sensitive request information is filtered before it reaches the investigation workflow.

Examples:

Authorization → [FILTERED]
API-Key       → [FILTERED]
Cookie        → [FILTERED]
Session data  → [FILTERED]

</details>

<details>
<summary><b>04 · 🗺️ Traceback → Source Mapping</b></summary>

A stack trace is mapped back to the relevant repository files.

Instead of giving AI only:

ValueError: quantity cannot be negative

the investigation receives the failure together with relevant source context.

</details>

<details>
<summary><b>05 · 🧠 Root-Cause Investigation</b></summary>

The AI analysis layer reasons over:

incident details

traceback frames

relevant source code

repository context

It returns structured hypotheses rather than a generic conversational answer.

</details>

<details>
<summary><b>06 · 🧪 Failure Reproduction</b></summary>

A reproducer is generated to demonstrate the failure.

The test is executed in an isolated verification environment rather than directly against the developer's working tree.

</details>

<details>
<summary><b>07 · 🩹 Patch Generation</b></summary>

After selecting a hypothesis, Agentless generates a candidate code patch.

The patch is treated as untrusted until verification succeeds.

</details>

<details>
<summary><b>08 · 🔬 Patch Verification</b></summary>

The verification engine:

creates a clean workspace

validates the patch

applies the patch

executes the reproducer

runs the existing test suite

determines whether the change is acceptable

</details>

<details>
<summary><b>09 · 🚀 GitHub Automation</b></summary>

After verification succeeds:

Create Branch
     ↓
Commit Fix
     ↓
Push Branch
     ↓
Create Pull Request

The final merge remains under developer control.

</details>

🎬 End-to-End Demo

Example: Negative quantity API failure

A sample API contains a failure where:

quantity = -1

causes an unhandled exception.

Agentless processes it as:

🚨 Production-style Failure
          ↓
📥 Incident Ingestion
          ↓
🧬 Fingerprint
          ↓
🗺️ Map Traceback → Source
          ↓
🧠 Root Cause Hypothesis
          ↓
🧪 Generate Reproducer
          ↓
🩹 Generate Patch
          ↓
🔬 git apply --check       ✅
          ↓
🔬 Apply Patch             ✅
          ↓
🧪 Reproducer              ✅
          ↓
🧪 Regression Suite        ✅
          ↓
🌿 Create Fix Branch       ✅
          ↓
📤 Push to GitHub          ✅
          ↓
🔗 Pull Request            ✅

Before

POST /orders
quantity=-1

❌ HTTP 500
Unhandled ValueError

After verified fix

POST /orders
quantity=-1

✅ HTTP 400
Expected client error

Result

The fix is not considered successful until the system executes it and proves the original failure is resolved.

📊 Verification Results

<div align="center">

Verification

Result

📥 Patch endpoint

✅ PASS

📦 Clean workspace

✅ PASS

🔎 git apply --check

✅ PASS

🩹 Patch application

✅ PASS

🧪 Reproducer

✅ PASS

🧪 Existing test suite

✅ PASS

🚨 Original failure resolved

✅ PASS

🌿 Fix branch

✅ PASS

📤 Git push

✅ PASS

🔗 Pull Request

✅ PASS

10 / 10 verification stages passed

</div>

🏗️ Architecture

flowchart TB

    subgraph CLIENT["🖥️ Client Layer"]
        UI["Next.js Dashboard"]
    end

    subgraph CORE["⚡ Agentless Core"]
        API["FastAPI API"]
        ING["Ingestion"]
        FP["Fingerprinting"]
        MAP["Traceback Mapper"]
        AI["AI Investigation"]
        REP["Reproduction"]
        PATCH["Patch Generator"]
        VER["Verification Engine"]
    end

    subgraph EXEC["📦 Execution Layer"]
        WS["Clean Git Workspace"]
        SB["Sandbox / Test Executor"]
    end

    subgraph EXT["🌐 External Systems"]
        LLM["OpenAI Provider"]
        GIT["Git"]
        GH["GitHub API"]
    end

    UI --> API
    API --> ING
    ING --> FP
    FP --> MAP
    MAP --> AI
    AI --> LLM
    AI --> REP
    AI --> PATCH
    REP --> VER
    PATCH --> VER
    VER --> WS
    WS --> SB
    VER --> GIT
    GIT --> GH

🛠️ Technology Stack

<div align="center">

Layer

Technology

🎨 Dashboard

Next.js + TypeScript

⚡ API

FastAPI

🐍 Runtime

Python 3.10+

🧠 AI

OpenAI-compatible provider

🐙 Version Control

Git + GitHub API

🔬 Verification

Git + Pytest

📦 Isolation

Sandbox / Docker execution

🗄️ Persistence

SQLAlchemy + SQLite-compatible setup

</div>

📁 Project Structure

agentless/
│
├── ⚡ backend/
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
├── 🎨 frontend/
│   ├── app/
│   │   ├── incidents/
│   │   ├── investigations/
│   │   ├── repositories/
│   │   └── pull-requests/
│   └── package.json
│
├── 🧪 sandbox/
│   └── sample_repo/
│
├── 📜 scripts/
├── 📚 docs/
├── 🔐 .env.example
├── 🛡️ .gitignore
└── 📖 README.md

🚀 Quick Start

1. Clone

git clone https://github.com/NITISH-027/agentless-api-observability.git
cd agentless-api-observability

2. Backend

cd backend

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

python -m uvicorn app.main:app --port 8000

API

http://127.0.0.1:8000

Swagger

http://127.0.0.1:8000/docs

3. Frontend

Open another terminal:

cd frontend
npm install
npm run dev

Dashboard:

http://localhost:3000

🧠 AI Provider Modes

Agentless supports both deterministic demonstration mode and live AI mode.

<table>
<tr>
<td width="50%">

🎭 Mock Mode

Designed for:

hackathon demos

deterministic testing

offline development

reproducible evaluation

LLM_PROVIDER=mock

</td>
<td width="50%">

🧠 Live Mode

Designed for genuine AI-powered investigation.

LLM_PROVIDER=openai
LLM_API_KEY=your_key

Requires an API key with available quota.

</td>
</tr>
</table>

Demo transparency: the current hackathon demonstration uses the deterministic mock provider for reproducibility. The workspace verification, patch application, test execution, Git operations and GitHub integration are real.

🧪 Testing

Backend:

cd backend
.venv\Scripts\pytest -q

Current backend suite:

63 tests

Frontend:

cd frontend
npm run build

🔐 Safety Model

Agentless is designed around controlled automation, not blind code execution.

🛡️ 1. Scrub sensitive data

Secrets and sensitive request information are filtered.

📦 2. Use an isolated workspace

Verification happens against a clean repository workspace.

🔬 3. Execute before accepting

A patch must pass:

Patch validation
      +
Reproducer
      +
Regression tests

👨‍💻 4. Keep humans in control

Agentless prepares the Pull Request.

A developer still decides whether it should be merged.

🏆 Why This Matters

The interesting part of Agentless is not simply:

"We added AI to debugging."

The interesting part is:

"We connected AI reasoning to deterministic software verification."

That changes the workflow from:

AI says:
"Here is a possible fix."

to:

AI says:
"Here is a possible fix."

System says:
"Let's execute it."

Tests say:
"It works."

GitHub says:
"Here is the PR."

📈 Current MVP Status

Capability

Status

📥 Failure ingestion

✅

🧬 Incident fingerprinting

✅

🛡️ Data scrubbing

✅

🗺️ Traceback mapping

✅

🧠 Hypothesis pipeline

✅

🧪 Reproduction pipeline

✅

🩹 Patch generation

✅

🔬 Patch verification

✅

🧪 Regression testing

✅

🌿 Git branch automation

✅

📤 Git push

✅

🔗 Pull Request creation

✅

🖥️ Web dashboard

✅

🎭 Mock LLM provider

✅

🧠 Live OpenAI provider

✅*

* Requires a funded API key with available quota.

🔗 Repository

<div align="center">

⚡ github.com/NITISH-027/agentless-api-observability

Read the code. Run the system. Inspect the verification flow.

</div>

👥 Team VULCAN

<div align="center">

🏫 Panimalar Engineering College · Chennai

</div>

Member

Responsibility

Nitish P

🧠 AI & Backend Engineering

Niranjan B

⚙️ Systems & Integration

Neal Patrick A

🎨 Frontend Engineering

<div align="center">

⚡ VULCAN × AGENTLESS

From production failure to verified Pull Request.

Built for PEC Hacks 4.0

<br>

AI proposes. Execution proves.

</div>
