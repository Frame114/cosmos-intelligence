# Architecture Decision Records

This file records important technical decisions and their rationale. Significant changes should include context, alternatives, consequences and a review date.

## ADR-001: Python for the backend

**Status:** Accepted  
**Decision:** Use Python 3.11+ for the backend and integration services.

**Rationale:** Python has mature HTTP, validation, testing, data engineering and AI/MCP ecosystems. It also supports the project's learning objectives.

**Consequences:** Pin supported dependency ranges, use type hints, linting, formatting and automated tests.

## ADR-002: FastAPI for the HTTP API

**Status:** Accepted  
**Decision:** Use FastAPI with Pydantic schemas.

**Rationale:** Typed request/response contracts, OpenAPI generation and asynchronous request handling suit an API integration platform.

## ADR-003: Verify NASA contracts before implementation

**Status:** Accepted  
**Decision:** Treat official NASA documentation and inspected live responses as the source of truth for each integration.

**Rationale:** API versions, endpoint ownership, response shapes and retirement dates can change. Do not build assumptions from old tutorials or cached examples.

**Consequence:** Keep response fixtures and contract tests, and record the date and source used for verification.

## ADR-004: Evidence-grounded AI output

**Status:** Accepted  
**Decision:** AI-generated explanations must distinguish source data from model interpretation and provide traceable source references.

**Rationale:** Scientific content must not present unsupported model-generated statements as observed facts.