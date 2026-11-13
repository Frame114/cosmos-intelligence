# Cosmos Intelligence

**An open-source scientific data platform for exploring NASA datasets, space-weather events, near-Earth objects and Earth-observation media.**

Cosmos Intelligence is a portfolio-grade AI engineering project built to demonstrate reliable API integration, data engineering, backend architecture, scientific data interpretation, MCP tool development and production deployment.

> **Project status:** Early development — the repository currently contains the project foundation. Features are added only when implemented and tested.

## Project goals

- Integrate official NASA data services through well-tested, resilient API clients.
- Validate and normalise external data before it enters the application.
- Store useful records for search, comparison and historical analysis.
- Present scientific information through a clear web dashboard.
- Add an evidence-grounded AI research assistant.
- Expose selected capabilities through a Model Context Protocol (MCP) server.
- Demonstrate professional engineering practices: tests, security, CI, documentation and reproducible deployment.

## Planned capabilities

| Area | Planned capability |
|---|---|
| Astronomy picture | Retrieve and explore NASA's Astronomy Picture of the Day |
| Near-Earth objects | Search and compare asteroid approach data |
| Space weather | Explore relevant DONKI event records |
| Earth events | Discover curated natural-event data through EONET |
| NASA media | Search the NASA Image and Video Library |
| Data platform | Normalisation, persistence, provenance and resilient ingestion |
| AI assistant | Generate source-grounded explanations and reports |
| MCP | Expose selected searches and analysis as typed tools |

## Architecture direction

- **Backend:** Python, FastAPI, Pydantic, HTTPX, SQLAlchemy and Alembic
- **Database:** PostgreSQL
- **Frontend:** React, TypeScript, Vite and Tailwind CSS
- **Charts:** Recharts
- **AI integration:** OpenRouter (optional; provider abstraction planned)
- **Agent interoperability:** MCP using the official Python SDK
- **Operations:** Docker, Docker Compose, GitHub Actions and Caddy for production HTTPS

The architecture will be delivered incrementally. The first working slice is a FastAPI health endpoint; the first NASA integration will follow after its live response contract has been inspected.

## NASA API compatibility

NASA API endpoints evolve. The project will verify current official documentation and live response contracts before implementing each integration. In particular, the legacy APOD API endpoint is being retired; the project will target NASA's replacement APOD endpoint rather than build on the retiring service.

Useful official resources:

- [NASA API portal](https://api.nasa.gov/)
- [NASA Science APOD API](https://science.nasa.gov/wp-json/wp/v2/apod-basic)
- [NASA Image and Video Library API](https://images-api.nasa.gov/)

## Quick start

Prerequisites: Python 3.11+, Git and an optional NASA API key.

1. Clone the repository:
   ```bash
   git clone https://github.com/Frame114/cosmos-intelligence.git
   cd cosmos-intelligence
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # Linux/macOS
   source .venv/bin/activate
   ```
3. Install development dependencies:
   ```bash
   python -m pip install --upgrade pip
   pip install -e ".[dev]"
   ```
4. Copy `.env.example` to `.env` when local configuration is needed. Never commit real credentials.
5. Run linting and tests:
   ```bash
   ruff check .
   pytest --cov=app --cov-report=term-missing
   ```
6. Start the API:
   ```bash
   uvicorn app.main:app --reload
   ```
   Then open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) or check [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

## Engineering principles

1. Verify external contracts against official documentation and live responses.
2. Treat all upstream API data as untrusted input.
3. Keep secrets out of source control, logs and test fixtures.
4. Use timeouts, bounded retries and explicit error handling for network calls.
5. Preserve source attribution and distinguish observed facts from AI-generated interpretation.
6. Test failure modes, not only successful responses.
7. Never describe a feature as complete until its tests and acceptance criteria pass.

## Project tracking

- [Project status](PROJECT_STATUS.md)
- [Roadmap](ROADMAP.md)
- [Architecture notes](docs/architecture/overview.md)
- [API research and integration notes](docs/integrations/nasa-api-notes.md)
- [Architecture decisions](DECISIONS.md)
- [Technical debt](TECHNICAL_DEBT.md)
- [Assessment rubric](ASSESSMENT.md)
- [Changelog](CHANGELOG.md)

## Contributing

Issues and pull requests are welcome. Please include tests for behaviour changes and update documentation when interfaces or setup instructions change.

## Data, attribution and licensing

This repository's source code is licensed under the MIT License. NASA datasets and media remain subject to their respective source terms, attribution requirements and usage restrictions. NASA is not affiliated with or endorsing this project. Verify asset-specific rights before redistributing media.

## Disclaimer

Cosmos Intelligence is an educational and research software project. It is not an official NASA product and does not provide authoritative operational, safety or scientific advice.
