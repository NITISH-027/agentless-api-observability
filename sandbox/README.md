# Isolated Execution Sandbox

This directory contains the Docker configuration, scripts, and isolation layers used to reproduce failure traces and verify candidate fixes in a safe, sandboxed environment.

## Design

Later stages will implement the reproduction service (`app/services/reproduction`) and verification service (`app/services/verification`) to:
1. Provision a lightweight container based on the `SANDBOX_IMAGE` (e.g. `python:3.10-slim`).
2. Clone the victim codebase inside the container.
3. Spin up mock backend services if necessary.
4. Reproduce the log failure locally.
5. Verify code patches against original tests.
