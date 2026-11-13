# Technical Debt and Open Decisions

Planned features are tracked as backlog work, not debt. This register contains existing implementation gaps and unresolved decisions that affect the path to a verified release.

| ID | Item | Impact | Priority | State |
|---|---|---|---|---|
| TD-001 | The repository has an early backend/APOD prototype, but no acceptance evidence is recorded here | Current code behavior and upstream contract fit are not release-verified | High | Open |
| TD-002 | Package metadata and CI use Python 3.11 while the target technology specification selects Python 3.12 | Build/deployment support decision is inconsistent | High | Open |
| TD-003 | Dependency ranges are not a fully resolved, reproducible lock strategy | Clean installs may resolve different compatible releases | Medium | Open |
| TD-004 | Full Docker Compose application is specified but not implemented or verified | No reproducible full-stack run path is evidenced | High | Open |
| TD-005 | APOD portal parameter summary and dedicated guide differ | Date query behavior must be verified before implementing date search | High | Open |
| OD-001 | NASA AI/SI wording and attribution for generated NASA-derived content need formal review | AI generation must remain disabled until resolved | High | Release gate |
| OD-002 | Production identity issuer and account policy are undecided | Public authenticated features cannot be released | Medium | Open |
| OD-003 | Map tile provider and usage terms are undecided | Production Earth-event map choice is unresolved | Medium | Open |

Recheck statuses against repository evidence during implementation. See [implementation backlog](docs/10-implementation/TASK_BACKLOG.md) for planned work and acceptance evidence.
