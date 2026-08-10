# Platform Architecture Diagram & Component Flows

This document details the high-level architecture and how the components interact during the automated debugging lifecycle.

## High Level Component Diagram

```
                 +-----------------------+
                 | External Client App   |
                 +-----------------------+
                             |
                             |  POST /logs (Structured Ingestion)
                             v
                 +-----------------------+
                 | FastAPI Backend API   |
                 +-----------------------+
                             |
         +-------------------+--------------------+
         |                   |                    |
         v                   v                    v
+-----------------+ +-----------------+ +-----------------+
| Ingestion       | | Database        | | GitHub          |
| Service         | | (Supabase/PG)   | | Service         |
+-----------------+ +-----------------+ +-----------------+
         |                   |                    |
         |                   v                    |
         |         +-----------------+            |
         |         | Next.js App     |            |
         |         | Dashboard UI    |            |
         |         +-----------------+            |
         |                                        |
         v                                        v
+-----------------+                      +-----------------+
| Analysis        |                      | Pull Request    |
| Service (LLM)   |                      | Service         |
+-----------------+                      +-----------------+
         |                                        ^
         v                                        |
+-----------------+                      +-----------------+
| Reproduction    |                      | Patching &      |
| Service         |                      | Verification    |
+-----------------+                      +-----------------+
         |                                        ^
         +--------------->  [Sandbox]  -----------+
                     (Isolated Docker Runner)
```

## Step-by-Step Execution Lifecycle

1. **Ingestion**: External app fires structured failure logs to `POST /logs`. The backend scrubs keys, hashes a stable fingerprint, and saves the log.
2. **Analysis**: The analysis service queries stack traces and source files using the GitHub API, feeding this to LLM hypothesis generators.
3. **Reproduction**: The reproduction service starts a Docker container sandbox, attempts to reproduce the exception based on hypothesis logs.
4. **Patching**: Generates a git diff patch matching the root-cause fix.
5. **Verification**: Applies the patch inside the sandbox to verify the error is resolved and that existing test suites pass.
6. **Delivery**: Submits the fix as a GitHub Pull Request and updates the Incident investigation status.
