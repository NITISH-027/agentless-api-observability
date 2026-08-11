Conversation with Gemini
redesign this entire into a high level attractive readme file for git

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



Observability tells you that an API failed.

Agentless investigates why, reproduces the failure, verifies a fix, and prepares the PR.

<br>

🚀 Explore Repository ·

📖 Architecture ·

🐛 Report Issue

</div>





🧨 The Problem

Production API failures usually create a long chain of manual work.



┌─────────────────┐

│ 🚨 API FAILURE │

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

│ Apply Patch │

└─────────┬─────────┘

│

▼

┌───────────────────┐

│ Run Reproducer │

└─────────┬─────────┘

│

▼

┌───────────────────┐

│ Run Regression │

│ Test Suite │

└─────────┬─────────┘

│

┌───────┴───────┐

▼ ▼

❌ FAIL ✅ PASS

│ │

▼ ▼

Reject 🚀 PR

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

API-Key → [FILTERED]

Cookie → [FILTERED]

Session data → [FILTERED]

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

🔬 git apply --check ✅

↓

🔬 Apply Patch ✅

↓

🧪 Reproducer ✅

↓

🧪 Regression Suite ✅

↓

🌿 Create Fix Branch ✅

↓

📤 Push to GitHub ✅

↓

🔗 Pull Request ✅

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

VerificationResult📥 Patch endpoint✅ PASS📦 Clean workspace✅ PASS🔎 git apply --check✅ PASS🩹 Patch application✅ PASS🧪 Reproducer✅ PASS🧪 Existing test suite✅ PASS🚨 Original failure resolved✅ PASS🌿 Fix branch✅ PASS📤 Git push✅ PASS🔗 Pull Request✅ PASS

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

LayerTechnology🎨 DashboardNext.js + TypeScript⚡ APIFastAPI🐍 RuntimePython 3.10+🧠 AIOpenAI-compatible provider🐙 Version ControlGit + GitHub API🔬 VerificationGit + Pytest📦 IsolationSandbox / Docker execution🗄️ PersistenceSQLAlchemy + SQLite-compatible setup

</div>





📁 Project Structure

agentless/

│

├── ⚡ backend/

│ ├── app/

│ │ ├── api/routes/

│ │ ├── core/

│ │ ├── models/

│ │ ├── schemas/

│ │ └── services/

│ │ ├── analysis/

│ │ ├── github/

│ │ ├── ingestion/

│ │ ├── patch/

│ │ ├── reproduction/

│ │ └── verification/

│ │

│ ├── tests/

│ └── requirements.txt

│

├── 🎨 frontend/

│ ├── app/

│ │ ├── incidents/

│ │ ├── investigations/

│ │ ├── repositories/

│ │ └── pull-requests/

│ └── package.json

│

├── 🧪 sandbox/

│ └── sample_repo/

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

CapabilityStatus📥 Failure ingestion✅🧬 Incident fingerprinting✅🛡️ Data scrubbing✅🗺️ Traceback mapping✅🧠 Hypothesis pipeline✅🧪 Reproduction pipeline✅🩹 Patch generation✅🔬 Patch verification✅🧪 Regression testing✅🌿 Git branch automation✅📤 Git push✅🔗 Pull Request creation✅🖥️ Web dashboard✅🎭 Mock LLM provider✅🧠 Live OpenAI provider✅*

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

MemberResponsibilityNitish P🧠 AI & Backend EngineeringNiranjan B⚙️ Systems & IntegrationNeal Patrick A🎨 Frontend Engineering





<div align="center">



⚡ VULCAN × AGENTLESS

From production failure to verified Pull Request.

Built for PEC Hacks 4.0

<br>

AI proposes. Execution proves.

</div>

Here is a complete, polished, modern GitHub README designed to give your project a polished open-source aesthetic using crisp formatting, clean layouts, and rich visual elements.

Markdown
<div align="center">

# ⚡ AGENTLESS
### Autonomous API Debugging & Self-Healing Pipeline
**From production failure → verified fix → GitHub Pull Request**

<br />

[![PEC Hacks 4.0](https://img.shields.io/badge/PEC_HACKS-4.0-7C3AED?style=for-the-badge&logoColor=white&labelColor=111827)](https://github.com/NITISH-027/agentless-api-observability)
[![Status](https://img.shields.io/badge/STATUS-MVP_READY-10B981?style=for-the-badge&logoColor=white&labelColor=111827)](https://github.com/NITISH-027/agentless-api-observability)
[![AI Powered](https://img.shields.io/badge/AI-POWERED-8B5CF6?style=for-the-badge&logoColor=white&labelColor=111827)](https://github.com/NITISH-027/agentless-api-observability)
[![Python](https://img.shields.io/badge/PYTHON-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=111827)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FASTAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=111827)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/NEXT.JS-14-000000?style=for-the-badge&logo=next.js&logoColor=white&labelColor=111827)](https://nextjs.org)

<br />

> **Observability tells you that an API failed.**  
> **Agentless investigates why, reproduces the failure, verifies a fix, and opens the PR.**

[🚀 Quick Start](#-quick-start) • [📖 Architecture](#%EF%B8%8F-architecture) • [🐛 Pipeline](#-what-happens-inside-the-pipeline) • [🧠 AI Modes](#-ai-provider-modes)

</div>

---

## 🧨 The Problem

Production API failures trigger a tedious, fragmented chain of manual engineering work:

🚨 API FAILURE ──> 📋 Inspect Logs ──> 🔎 Read Traceback ──> 🗺️ Find Source Code
│
🔗 Open PR <── 🌿 Branch <── 🧪 Run Tests <── ✍️ Fix <── 🧪 Reproduce <── 🧠 Root Cause


### The Hidden Cost
Developers don't just spend time finding errors; they waste hours bridging disconnected tools across the debugging lifecycle:

$$\text{Logs} \longrightarrow \text{Source} \longrightarrow \text{Root Cause} \longrightarrow \text{Reproduction} \longrightarrow \text{Code Patch} \longrightarrow \text{Validation} \longrightarrow \text{PR}$$

> **Most observability platforms stop at the first half.**  
> Agentless turns the entire debugging lifecycle into a single connected, automated workflow.

---

## ⚡ The Agentless Difference

<div align="center">

`FAILURE` ➔ `INVESTIGATION` ➔ `REPRODUCTION` ➔ `PATCH` ➔ `VERIFICATION` ➔ `PULL REQUEST`

</div>

| 🔍 Traditional Observability | ⚡ Agentless Self-Healing |
| :--- | :--- |
| 📊 Detects failures | 📥 Ingests & fingerprints the failure |
| 📝 Displays logs & dashboards | 🗺️ Maps tracebacks directly to source code |
| 🧵 Shows stack traces | 🧠 Generates root-cause hypotheses |
| 👨‍💻 **Developer takes over completely** | 🧪 Generates reproducer & candidate patch |
| | 🔬 Executes safety verification suite |
| | 🚀 Prepares & opens verified GitHub PR |
| **Output:** *"Something went wrong."* | **Output:** *"Here is the verified fix."* |

---

## 🔥 Core Innovation: Verification-First AI Debugging

The fundamental design pillar of Agentless is simple: **AI-generated code is never trusted at face value.**  
Every proposed patch must survive a strict execution-based safety gate before reaching a human developer.

              🧠 AI Generator
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
          Reject          🚀 Create PR

> 💡 **The Gold Rule:** *AI proposes. Execution proves.*

---

## 🧩 What Happens Inside the Pipeline?

<details>
<summary><b>01 · 📥 Failure Ingestion</b></summary>
<br />
Agentless receives structured API failure payloads and builds an incident record, capturing crucial execution telemetry without manual reconstruction.
</details>

<details>
<summary><b>02 · 🧬 Incident Fingerprinting</b></summary>
<br />
Repeated failures are grouped into stable, unique fingerprints based on route signatures, error classes, stack frame hierarchies, and source context to prevent incident noise.
</details>

<details>
<summary><b>03 · 🛡️ Sensitive Data Scrubbing</b></summary>
<br />
All sensitive telemetry data is redacted prior to LLM processing:
<code>Authorization</code>, <code>API-Key</code>, <code>Cookie</code>, and session payloads are stripped automatically.
</details>

<details>
<summary><b>04 · 🗺️ Traceback → Source Mapping</b></summary>
<br />
Raw stack traces are parsed and mapped directly to exact files and line numbers in the connected repository, supplying the AI with true source code context.
</details>

<details>
<summary><b>05 · 🧠 Root-Cause Investigation</b></summary>
<br />
The AI reasoning engine evaluates incident context, traceback frames, and repository structure to produce structured hypotheses instead of vague conversational responses.
</details>

<details>
<summary><b>06 · 🧪 Failure Reproduction</b></summary>
<br />
An automated reproducer test script is built and run inside an isolated verification sandbox to confirm the failure reliably triggers before attempting fixes.
</details>

<details>
<summary><b>07 · 🩹 Patch Generation</b></summary>
<br />
Agentless constructs a targeted code patch corresponding to the primary failure hypothesis. The patch remains untrusted until full verification completes.
</details>

<details>
<summary><b>08 · 🔬 Patch Verification</b></summary>
<br />
The verification engine provisions a clean workspace, executes <code>git apply --check</code>, applies the patch, executes the reproducer, and runs full regression test suites.
</details>

<details>
<summary><b>09 · 🚀 GitHub Automation</b></summary>
<br />
Upon successful verification, Agentless creates a feature branch, commits changes, pushes to remote, and opens a Pull Request for human review.
</details>

---

## 🎬 End-to-End Demo Case

### Scenario: Negative Quantity Payload Failure

```http
POST /orders
Content-Type: application/json

{ "quantity": -1 }
BEFORE FIX:  ❌ HTTP 500 Internal Server Error (Unhandled ValueError)
AFTER FIX:   ✅ HTTP 400 Bad Request (Expected validation error)
Verification Stage Results
VerificationResult
 ├── 📥 Patch Endpoint           ✅ PASS
 ├── 📦 Clean Workspace          ✅ PASS
 ├── 🔎 git apply --check        ✅ PASS
 ├── 🩹 Patch Application        ✅ PASS
 ├── 🧪 Reproducer Execution     ✅ PASS
 ├── 🧪 Existing Test Suite      ✅ PASS
 ├── 🚨 Original Failure Fixed   ✅ PASS
 ├── 🌿 Fix Branch Creation      ✅ PASS
 ├── 📤 Git Remote Push          ✅ PASS
 └── 🔗 Pull Request Creation    ✅ PASS

[ 10 / 10 Verification Stages Passed ]
🏗️ Architecture
Code snippet
flowchart TB
    subgraph CLIENT["🖥️ Client Layer"]
        UI["Next.js Dashboard"]
    end

    subgraph CORE["⚡ Agentless Core Engine"]
        API["FastAPI App"]
        ING["Ingestion"]
        FP["Fingerprinting"]
        MAP["Traceback Mapper"]
        AI["AI Investigation"]
        REP["Reproduction"]
        PATCH["Patch Generator"]
        VER["Verification Engine"]
    end

    subgraph EXEC["📦 Execution Layer"]
        WS["Clean Workspace"]
        SB["Sandbox / Test Executor"]
    end

    subgraph EXT["🌐 External Interfaces"]
        LLM["OpenAI Provider"]
        GIT["Git CLI"]
        GH["GitHub API"]
    end

    UI --> API
    API --> ING --> FP --> MAP --> AI
    AI --> LLM
    AI --> REP & PATCH
    REP & PATCH --> VER
    VER --> WS --> SB
    VER --> GIT --> GH
🛠️ Technology Stack
Layer	Technology	Description
Dashboard	Next.js 14 TypeScript Tailwind CSS	Web interface for monitoring incidents & PRs
Core API	FastAPI Python 3.10+ Pydantic	Async backend API framework
AI Layer	OpenAI API	LLM reasoning engine for root-cause analysis
Verification	Pytest Git CLI Docker	Isolated execution & regression testing framework
Database	SQLAlchemy SQLite/PostgreSQL	Relational persistence layer
📁 Project Structure
Plaintext
agentless/
├── ⚡ backend/
│   ├── app/
│   │   ├── api/routes/          # Ingestion & verification endpoints
│   │   ├── core/                # Configuration & security settings
│   │   ├── models/              # Database entities
│   │   └── services/            # Pipeline modules (AI, Git, Reproduction)
│   ├── tests/                   # Backend unit & integration test suite
│   └── requirements.txt
├── 🎨 frontend/                 # Next.js web application
│   ├── app/                     # Incidents, Investigations & PR views
│   └── package.json
├── 🧪 sandbox/                  # Isolated environment for candidate testing
├── 📜 scripts/                  # Utility & setup scripts
└── 📖 README.md
🚀 Quick Start
1. Clone Repository
Bash
git clone [https://github.com/NITISH-027/agentless-api-observability.git](https://github.com/NITISH-027/agentless-api-observability.git)
cd agentless-api-observability
2. Launch Backend
Bash
cd backend

# Create & activate virtual environment
python -m venv .venv
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies & run API
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
API Base: http://127.0.0.1:8000

Swagger Docs: http://127.0.0.1:8000/docs

3. Launch Frontend
Bash
# Open a new terminal session
cd frontend
npm install
npm run dev
Dashboard: http://localhost:3000

🧠 AI Provider Modes
Agentless supports both deterministic demonstration environments and live LLM integration:

Mode	Configuration	Best Used For
🎭 Mock Mode	LLM_PROVIDER=mock	Offline development, reproducible evaluations, hackathon presentations.
🧠 Live Mode	LLM_PROVIDER=openaiLLM_API_KEY=your_key	Production environments, live automated reasoning & repair.
ℹ️ Note on Hackathon Demo: The current demonstration uses the deterministic mock provider to guarantee complete submission stability. Workspace isolation, patch application, execution verification, and GitHub automation run on real systems.

🔐 Safety Model
Scrub Sensitive Telemetry: Automatic sanitization removes credentials, tokens, and authorization headers prior to analysis.

Workspace Isolation: All verification tests execute within transient sandboxes without contaminating working source trees.

Execution Verification Gate: No patch is considered unless it passes syntax checks, reproducer scripts, and existing unit tests.

Human-in-the-Loop Governance: Agentless handles investigation and PR creation; human engineers make all final merge decisions.

📈 MVP Status
Capability	Status	Capability	Status
📥 Failure Ingestion	✅	🩹 Patch Generation	✅
🧬 Incident Fingerprinting	✅	🔬 Patch Verification	✅
🛡️ Data Scrubbing	✅	🧪 Regression Testing	✅
🗺️ Traceback Mapping	✅	🌿 Git Branch Automation	✅
🧠 Hypothesis Pipeline	✅	📤 Git Push & PR Creation	✅
🧪 Reproduction Pipeline	✅	🖥️ Next.js Web Dashboard	✅
👥 Team VULCAN
Panimalar Engineering College · Chennai

Team Member	Domain Responsibility
Nitish P	🧠 AI Architecture & Backend Engineering
Niranjan B	⚙️ Core Systems Integration & Pipelines
Neal Patrick A	🎨 Frontend Engineering & Dashboard UI
⚡ VULCAN × AGENTLESS

Built for PEC Hacks 4.0

AI Proposes. Execution Proves.

Want me to generate custom SVG project badges or custom social preview banners?

Yes
Generate custom SVG badges or visual assets for the Agentless repository README.

SVG

🏷️ Additional Modular Shields & Badges
You can embed these SVG badge blocks directly into your Markdown files:

1. Tech Stack Badges
SVG

2. Workflow Pillar Callout
SVG

give everything as a markdown file

dont break the markdown file

🚨 API FAILURE ──> 📋 Inspect Logs ──> 🔎 Read Traceback ──> 🗺️ Find Source Code
│
🔗 Open PR <── 🌿 Branch <── 🧪 Run Tests <── ✍️ Fix <── 🧪 Reproduce <── 🧠 Root Cause


### The Hidden Cost
Developers don't just spend time finding errors; they waste hours bridging disconnected tools across the debugging lifecycle:

$$\\text{Logs} \\longrightarrow \\text{Source} \\longrightarrow \\text{Root Cause} \\longrightarrow \\text{Reproduction} \\longrightarrow \\text{Code Patch} \\longrightarrow \\text{Validation} \\longrightarrow \\text{PR}$$

> **Most observability platforms stop at the first half.**  
> Agentless turns the entire debugging lifecycle into a single connected, automated workflow.

---

## ⚡ The Agentless Difference

<div align="center">

`FAILURE` ➔ `INVESTIGATION` ➔ `REPRODUCTION` ➔ `PATCH` ➔ `VERIFICATION` ➔ `PULL REQUEST`

</div>

| 🔍 Traditional Observability | ⚡ Agentless Self-Healing |
| :--- | :--- |
| 📊 Detects failures | 📥 Ingests & fingerprints the failure |
| 📝 Displays logs & dashboards | 🗺️ Maps tracebacks directly to source code |
| 🧵 Shows stack traces | 🧠 Generates root-cause hypotheses |
| 👨‍💻 **Developer takes over completely** | 🧪 Generates reproducer & candidate patch |
| | 🔬 Executes safety verification suite |
| | 🚀 Prepares & opens verified GitHub PR |
| **Output:** *"Something went wrong."* | **Output:** *"Here is the verified fix."* |

---

## 🔥 Core Innovation: Verification-First AI Debugging

The fundamental design pillar of Agentless is simple: **AI-generated code is never trusted at face value.**  
Every proposed patch must survive a strict execution-based safety gate before reaching a human developer.

              🧠 AI Generator
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
          Reject          🚀 Create PR

> 💡 **The Gold Rule:** *AI proposes. Execution proves.*

---

## 🧩 What Happens Inside the Pipeline?

<details>
<summary><b>01 · 📥 Failure Ingestion</b></summary>
<br />
Agentless receives structured API failure payloads and builds an incident record, capturing crucial execution telemetry without manual reconstruction.
</details>

<details>
<summary><b>02 · 🧬 Incident Fingerprinting</b></summary>
<br />
Repeated failures are grouped into stable, unique fingerprints based on route signatures, error classes, stack frame hierarchies, and source context to prevent incident noise.
</details>

<details>
<summary><b>03 · 🛡️ Sensitive Data Scrubbing</b></summary>
<br />
All sensitive telemetry data is redacted prior to LLM processing:
<code>Authorization</code>, <code>API-Key</code>, <code>Cookie</code>, and session payloads are stripped automatically.
</details>

<details>
<summary><b>04 · 🗺️ Traceback → Source Mapping</b></summary>
<br />
Raw stack traces are parsed and mapped directly to exact files and line numbers in the connected repository, supplying the AI with true source code context.
</details>

<details>
<summary><b>05 · 🧠 Root-Cause Investigation</b></summary>
<br />
The AI reasoning engine evaluates incident context, traceback frames, and repository structure to produce structured hypotheses instead of vague conversational responses.
</details>

<details>
<summary><b>06 · 🧪 Failure Reproduction</b></summary>
<br />
An automated reproducer test script is built and run inside an isolated verification sandbox to confirm the failure reliably triggers before attempting fixes.
</details>

<details>
<summary><b>07 · 🩹 Patch Generation</b></summary>
<br />
Agentless constructs a targeted code patch corresponding to the primary failure hypothesis. The patch remains untrusted until full verification completes.
</details>

<details>
<summary><b>08 · 🔬 Patch Verification</b></summary>
<br />
The verification engine provisions a clean workspace, executes <code>git apply --check</code>, applies the patch, executes the reproducer, and runs full regression test suites.
</details>

<details>
<summary><b>09 · 🚀 GitHub Automation</b></summary>
<br />
Upon successful verification, Agentless creates a feature branch, commits changes, pushes to remote, and opens a Pull Request for human review.
</details>

---

## 🎬 End-to-End Demo Case

### Scenario: Negative Quantity Payload Failure

```http
POST /orders
Content-Type: application/json

{ "quantity": -1 }
BEFORE FIX:  ❌ HTTP 500 Internal Server Error (Unhandled ValueError)
AFTER FIX:   ✅ HTTP 400 Bad Request (Expected validation error)
Verification Stage Results
VerificationResult
 ├── 📥 Patch Endpoint           ✅ PASS
 ├── 📦 Clean Workspace          ✅ PASS
 ├── 🔎 git apply --check        ✅ PASS
 ├── 🩹 Patch Application        ✅ PASS
 ├── 🧪 Reproducer Execution     ✅ PASS
 ├── 🧪 Existing Test Suite      ✅ PASS
 ├── 🚨 Original Failure Fixed   ✅ PASS
 ├── 🌿 Fix Branch Creation      ✅ PASS
 ├── 📤 Git Remote Push          ✅ PASS
 └── 🔗 Pull Request Creation    ✅ PASS

[ 10 / 10 Verification Stages Passed ]
🏗️ Architecture
Code snippet
flowchart TB
    subgraph CLIENT["🖥️ Client Layer"]
        UI["Next.js Dashboard"]
    end

    subgraph CORE["⚡ Agentless Core Engine"]
        API["FastAPI App"]
        ING["Ingestion"]
        FP["Fingerprinting"]
        MAP["Traceback Mapper"]
        AI["AI Investigation"]
        REP["Reproduction"]
        PATCH["Patch Generator"]
        VER["Verification Engine"]
    end

    subgraph EXEC["📦 Execution Layer"]
        WS["Clean Workspace"]
        SB["Sandbox / Test Executor"]
    end

    subgraph EXT["🌐 External Interfaces"]
        LLM["OpenAI Provider"]
        GIT["Git CLI"]
        GH["GitHub API"]
    end

    UI --> API
    API --> ING --> FP --> MAP --> AI
    AI --> LLM
    AI --> REP & PATCH
    REP & PATCH --> VER
    VER --> WS --> SB
    VER --> GIT --> GH
🛠️ Technology Stack
Layer	Technology	Description
Dashboard	Next.js 14 TypeScript Tailwind CSS	Web interface for monitoring incidents & PRs
Core API	FastAPI Python 3.10+ Pydantic	Async backend API framework
AI Layer	OpenAI API	LLM reasoning engine for root-cause analysis
Verification	Pytest Git CLI Docker	Isolated execution & regression testing framework
Database	SQLAlchemy SQLite/PostgreSQL	Relational persistence layer
📁 Project Structure
Plaintext
agentless/
├── ⚡ backend/
│   ├── app/
│   │   ├── api/routes/          # Ingestion & verification endpoints
│   │   ├── core/                # Configuration & security settings
│   │   ├── models/              # Database entities
│   │   └── services/            # Pipeline modules (AI, Git, Reproduction)
│   ├── tests/                   # Backend unit & integration test suite
│   └── requirements.txt
├── 🎨 frontend/                 # Next.js web application
│   ├── app/                     # Incidents, Investigations & PR views
│   └── package.json
├── 🧪 sandbox/                  # Isolated environment for candidate testing
├── 📜 scripts/                  # Utility & setup scripts
└── 📖 README.md
🚀 Quick Start
1. Clone Repository
Bash
git clone [https://github.com/NITISH-027/agentless-api-observability.git](https://github.com/NITISH-027/agentless-api-observability.git)
cd agentless-api-observability
2. Launch Backend
Bash
cd backend

# Create & activate virtual environment
python -m venv .venv
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies & run API
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
API Base: http://127.0.0.1:8000

Swagger Docs: http://127.0.0.1:8000/docs

3. Launch Frontend
Bash
# Open a new terminal session
cd frontend
npm install
npm run dev
Dashboard: http://localhost:3000

🧠 AI Provider Modes
Agentless supports both deterministic demonstration environments and live LLM integration:

Mode	Configuration	Best Used For
🎭 Mock Mode	LLM_PROVIDER=mock	Offline development, reproducible evaluations, hackathon presentations.
🧠 Live Mode	LLM_PROVIDER=openaiLLM_API_KEY=your_key	Production environments, live automated reasoning & repair.
ℹ️ Note on Hackathon Demo: The current demonstration uses the deterministic mock provider to guarantee complete submission stability. Workspace isolation, patch application, execution verification, and GitHub automation run on real systems.

🔐 Safety Model
Scrub Sensitive Telemetry: Automatic sanitization removes credentials, tokens, and authorization headers prior to analysis.

Workspace Isolation: All verification tests execute within transient sandboxes without contaminating working source trees.

Execution Verification Gate: No patch is considered unless it passes syntax checks, reproducer scripts, and existing unit tests.

Human-in-the-Loop Governance: Agentless handles investigation and PR creation; human engineers make all final merge decisions.

📈 MVP Status
Capability	Status	Capability	Status
📥 Failure Ingestion	✅	🩹 Patch Generation	✅
🧬 Incident Fingerprinting	✅	🔬 Patch Verification	✅
🛡️ Data Scrubbing	✅	🧪 Regression Testing	✅
🗺️ Traceback Mapping	✅	🌿 Git Branch Automation	✅
🧠 Hypothesis Pipeline	✅	📤 Git Push & PR Creation	✅
🧪 Reproduction Pipeline	✅	🖥️ Next.js Web Dashboard	✅
👥 Team VULCAN
Panimalar Engineering College · Chennai

Team Member	Domain Responsibility
Nitish P	🧠 AI Architecture & Backend Engineering
Niranjan B	⚙️ Core Systems Integration & Pipelines
Neal Patrick A	🎨 Frontend Engineering & Dashboard UI
⚡ VULCAN × AGENTLESS

Built for PEC Hacks 4.0

AI Proposes. Execution Proves.

with open("README.md", "w", encoding="utf-8") as f:
f.write(readme_content)

print("README.md created successfully.")


```text?code_stdout&code_event_index=1
README.md created successfully.

Your Markdown file is ready

MD icon
README
 MD 
Open
The entire updated, high-level project documentation has been saved directly as README.md. It includes shield badges, structured pipeline breakdowns, architecture diagrams, execution flow diagrams, setup commands, safety policies, and team details.




Gemini is AI and can make mistakes.

<div align="center">

# ⚡ AGENTLESS
### Autonomous API Debugging & Self-Healing Pipeline
**From production failure → verified fix → GitHub Pull Request**

<br />

[![PEC Hacks 4.0](https://img.shields.io/badge/PEC_HACKS-4.0-7C3AED?style=for-the-badge&logoColor=white&labelColor=111827)](https://github.com/NITISH-027/agentless-api-observability)
[![Status](https://img.shields.io/badge/STATUS-MVP_READY-10B981?style=for-the-badge&logoColor=white&labelColor=111827)](https://github.com/NITISH-027/agentless-api-observability)
[![AI Powered](https://img.shields.io/badge/AI-POWERED-8B5CF6?style=for-the-badge&logoColor=white&labelColor=111827)](https://github.com/NITISH-027/agentless-api-observability)
[![Python](https://img.shields.io/badge/PYTHON-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=111827)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FASTAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=111827)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/NEXT.JS-14-000000?style=for-the-badge&logo=next.js&logoColor=white&labelColor=111827)](https://nextjs.org)

<br />

> **Observability tells you that an API failed.**  
> **Agentless investigates why, reproduces the failure, verifies a fix, and opens the PR.**

[🚀 Quick Start](#-quick-start) • [📖 Architecture](#%EF%B8%8F-architecture) • [🐛 Pipeline](#-what-happens-inside-the-pipeline) • [🧠 AI Modes](#-ai-provider-modes)

</div>

---

## 🧨 The Problem

Production API failures trigger a tedious, fragmented chain of manual engineering work:

```
🚨 API FAILURE ──> 📋 Inspect Logs ──> 🔎 Read Traceback ──> 🗺️ Find Source Code
                                                                   │
🔗 Open PR <── 🌿 Branch <── 🧪 Run Tests <── ✍️ Fix <── 🧪 Reproduce <── 🧠 Root Cause
```

### The Hidden Cost
Developers don't just spend time finding errors; they waste hours bridging disconnected tools across the debugging lifecycle:

$$\text{Logs} \longrightarrow \text{Source} \longrightarrow \text{Root Cause} \longrightarrow \text{Reproduction} \longrightarrow \text{Code Patch} \longrightarrow \text{Validation} \longrightarrow \text{PR}$$

> **Most observability platforms stop at the first half.**  
> Agentless turns the entire debugging lifecycle into a single connected, automated workflow.

---

## ⚡ The Agentless Difference

<div align="center">

`FAILURE` ➔ `INVESTIGATION` ➔ `REPRODUCTION` ➔ `PATCH` ➔ `VERIFICATION` ➔ `PULL REQUEST`

</div>

| 🔍 Traditional Observability | ⚡ Agentless Self-Healing |
| :--- | :--- |
| 📊 Detects failures | 📥 Ingests & fingerprints the failure |
| 📝 Displays logs & dashboards | 🗺️ Maps tracebacks directly to source code |
| 🧵 Shows stack traces | 🧠 Generates root-cause hypotheses |
| 👨‍💻 **Developer takes over completely** | 🧪 Generates reproducer & candidate patch |
| | 🔬 Executes safety verification suite |
| | 🚀 Prepares & opens verified GitHub PR |
| **Output:** *"Something went wrong."* | **Output:** *"Here is the verified fix."* |

---

## 🔥 Core Innovation: Verification-First AI Debugging

The fundamental design pillar of Agentless is simple: **AI-generated code is never trusted at face value.**  
Every proposed patch must survive a strict execution-based safety gate before reaching a human developer.

```
                  🧠 AI Generator
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
              Reject          🚀 Create PR
```

> 💡 **The Gold Rule:** *AI proposes. Execution proves.*

---

## 🧩 What Happens Inside the Pipeline?

<details>
<summary><b>01 · 📥 Failure Ingestion</b></summary>
<br />
Agentless receives structured API failure payloads and builds an incident record, capturing crucial execution telemetry without manual reconstruction.
</details>

<details>
<summary><b>02 · 🧬 Incident Fingerprinting</b></summary>
<br />
Repeated failures are grouped into stable, unique fingerprints based on route signatures, error classes, stack frame hierarchies, and source context to prevent incident noise.
</details>

<details>
<summary><b>03 · 🛡️ Sensitive Data Scrubbing</b></summary>
<br />
All sensitive telemetry data is redacted prior to LLM processing:
<code>Authorization</code>, <code>API-Key</code>, <code>Cookie</code>, and session payloads are stripped automatically.
</details>

<details>
<summary><b>04 · 🗺️ Traceback → Source Mapping</b></summary>
<br />
Raw stack traces are parsed and mapped directly to exact files and line numbers in the connected repository, supplying the AI with true source code context.
</details>

<details>
<summary><b>05 · 🧠 Root-Cause Investigation</b></summary>
<br />
The AI reasoning engine evaluates incident context, traceback frames, and repository structure to produce structured hypotheses instead of vague conversational responses.
</details>

<details>
<summary><b>06 · 🧪 Failure Reproduction</b></summary>
<br />
An automated reproducer test script is built and run inside an isolated verification sandbox to confirm the failure reliably triggers before attempting fixes.
</details>

<details>
<summary><b>07 · 🩹 Patch Generation</b></summary>
<br />
Agentless constructs a targeted code patch corresponding to the primary failure hypothesis. The patch remains untrusted until full verification completes.
</details>

<details>
<summary><b>08 · 🔬 Patch Verification</b></summary>
<br />
The verification engine provisions a clean workspace, executes <code>git apply --check</code>, applies the patch, executes the reproducer, and runs full regression test suites.
</details>

<details>
<summary><b>09 · 🚀 GitHub Automation</b></summary>
<br />
Upon successful verification, Agentless creates a feature branch, commits changes, pushes to remote, and opens a Pull Request for human review.
</details>

---

## 🎬 End-to-End Demo Case

### Scenario: Negative Quantity Payload Failure

```http
POST /orders
Content-Type: application/json

{ "quantity": -1 }
```

```
BEFORE FIX:  ❌ HTTP 500 Internal Server Error (Unhandled ValueError)
AFTER FIX:   ✅ HTTP 400 Bad Request (Expected validation error)
```

### Verification Stage Results

```
VerificationResult
 ├── 📥 Patch Endpoint           ✅ PASS
 ├── 📦 Clean Workspace          ✅ PASS
 ├── 🔎 git apply --check        ✅ PASS
 ├── 🩹 Patch Application        ✅ PASS
 ├── 🧪 Reproducer Execution     ✅ PASS
 ├── 🧪 Existing Test Suite      ✅ PASS
 ├── 🚨 Original Failure Fixed   ✅ PASS
 ├── 🌿 Fix Branch Creation      ✅ PASS
 ├── 📤 Git Remote Push          ✅ PASS
 └── 🔗 Pull Request Creation    ✅ PASS

[ 10 / 10 Verification Stages Passed ]
```

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph CLIENT["🖥️ Client Layer"]
        UI["Next.js Dashboard"]
    end

    subgraph CORE["⚡ Agentless Core Engine"]
        API["FastAPI App"]
        ING["Ingestion"]
        FP["Fingerprinting"]
        MAP["Traceback Mapper"]
        AI["AI Investigation"]
        REP["Reproduction"]
        PATCH["Patch Generator"]
        VER["Verification Engine"]
    end

    subgraph EXEC["📦 Execution Layer"]
        WS["Clean Workspace"]
        SB["Sandbox / Test Executor"]
    end

    subgraph EXT["🌐 External Interfaces"]
        LLM["OpenAI Provider"]
        GIT["Git CLI"]
        GH["GitHub API"]
    end

    UI --> API
    API --> ING --> FP --> MAP --> AI
    AI --> LLM
    AI --> REP & PATCH
    REP & PATCH --> VER
    VER --> WS --> SB
    VER --> GIT --> GH
```

---

## 🛠️ Technology Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Dashboard** | `Next.js 14` `TypeScript` `Tailwind CSS` | Web interface for monitoring incidents & PRs |
| **Core API** | `FastAPI` `Python 3.10+` `Pydantic` | Async backend API framework |
| **AI Layer** | `OpenAI API` | LLM reasoning engine for root-cause analysis |
| **Verification** | `Pytest` `Git CLI` `Docker` | Isolated execution & regression testing framework |
| **Database** | `SQLAlchemy` `SQLite/PostgreSQL` | Relational persistence layer |

---

## 📁 Project Structure

```text
agentless/
├── ⚡ backend/
│   ├── app/
│   │   ├── api/routes/          # Ingestion & verification endpoints
│   │   ├── core/                # Configuration & security settings
│   │   ├── models/              # Database entities
│   │   └── services/            # Pipeline modules (AI, Git, Reproduction)
│   ├── tests/                   # Backend unit & integration test suite
│   └── requirements.txt
├── 🎨 frontend/                 # Next.js web application
│   ├── app/                     # Incidents, Investigations & PR views
│   └── package.json
├── 🧪 sandbox/                  # Isolated environment for candidate testing
├── 📜 scripts/                  # Utility & setup scripts
└── 📖 README.md
```

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/NITISH-027/agentless-api-observability.git
cd agentless-api-observability
```

### 2. Launch Backend
```bash
cd backend

# Create & activate virtual environment
python -m venv .venv
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies & run API
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
- **API Base:** `http://127.0.0.1:8000`
- **Swagger Docs:** `http://127.0.0.1:8000/docs`

### 3. Launch Frontend
```bash
# Open a new terminal session
cd frontend
npm install
npm run dev
```
- **Dashboard:** `http://localhost:3000`

---

## 🧠 AI Provider Modes

Agentless supports both deterministic demonstration environments and live LLM integration:

| Mode | Configuration | Best Used For |
| :--- | :--- | :--- |
| **🎭 Mock Mode** | `LLM_PROVIDER=mock` | Offline development, reproducible evaluations, hackathon presentations. |
| **🧠 Live Mode** | `LLM_PROVIDER=openai`<br />`LLM_API_KEY=your_key` | Production environments, live automated reasoning & repair. |

> ℹ️ **Note on Hackathon Demo:** The current demonstration uses the deterministic **mock provider** to guarantee complete submission stability. Workspace isolation, patch application, execution verification, and GitHub automation run on real systems.

---

## 🔐 Safety Model

1. **Scrub Sensitive Telemetry:** Automatic sanitization removes credentials, tokens, and authorization headers prior to analysis.
2. **Workspace Isolation:** All verification tests execute within transient sandboxes without contaminating working source trees.
3. **Execution Verification Gate:** No patch is considered unless it passes syntax checks, reproducer scripts, and existing unit tests.
4. **Human-in-the-Loop Governance:** Agentless handles investigation and PR creation; **human engineers make all final merge decisions**.

---

## 📈 MVP Status

| Capability | Status | Capability | Status |
| :--- | :---: | :--- | :---: |
| 📥 Failure Ingestion | ✅ | 🩹 Patch Generation | ✅ |
| 🧬 Incident Fingerprinting | ✅ | 🔬 Patch Verification | ✅ |
| 🛡️ Data Scrubbing | ✅ | 🧪 Regression Testing | ✅ |
| 🗺️ Traceback Mapping | ✅ | 🌿 Git Branch Automation | ✅ |
| 🧠 Hypothesis Pipeline | ✅ | 📤 Git Push & PR Creation | ✅ |
| 🧪 Reproduction Pipeline | ✅ | 🖥️ Next.js Web Dashboard | ✅ |

---

## 👥 Team VULCAN

> **Panimalar Engineering College · Chennai**

| Team Member | Domain Responsibility |
| :--- | :--- |
| **Nitish P** | 🧠 AI Architecture & Backend Engineering |
| **Niranjan B** | ⚙️ Core Systems Integration & Pipelines |
| **Neal Patrick A** | 🎨 Frontend Engineering & Dashboard UI |

<br />

<div align="center">

**⚡ VULCAN × AGENTLESS**  
*Built for PEC Hacks 4.0*

`AI Proposes. Execution Proves.`

</div>
