# Technical Debt and Open Decisions

Planned features are tracked as backlog work, not debt. This register lists implementation gaps and unresolved decisions that affect a verified release.

| ID | Item | Impact | Priority | State |
|---|---|---|---|---|
| TD-001 | The local service has PostgreSQL route tests for main listings, comparison, stored summaries, media detail, and owner boundaries, but several detail/error/provenance branches and browser journeys lack acceptance coverage | Product behavior remains only partly verified; latest backend coverage is 66% | High | In progress |
| TD-002 | Python package metadata, CI, and backend image previously disagreed on supported runtime | Python 3.12 is now used consistently; keep the patch current | High | Resolved; review updates |
| TD-003 | Backend dependencies use compatible ranges without a reproducible lock file | Clean image rebuilds may resolve different packages | Medium | Open |
| TD-004 | The local Compose slice is implemented, but there is no production overlay, TLS/domain config, persistent certificate state, or file-backed Compose secret mount | No production deployment path is verified | High | Partial |
| TD-005 | APOD portal summary and dedicated date guide differed | Implementation follows the dedicated guide's date contract and has a contract test | High | Resolved; recheck NASA contract |
| TD-006 | PostgreSQL enqueue/claim, lease recovery/retries, worker process, heartbeat loop, bounded APOD/NeoWs/DONKI/EONET handlers, and repeat-safe daily schedules are implemented; schedules remain disabled by default, while lease-loss runtime tests, job visibility, NASA Media job inputs, and API-to-worker cutover remain | NASA reads still happen in request handlers and the default local runtime does not enqueue jobs automatically | High | Partial |
| TD-007 | OIDC JWT validation is wired to protected REST routes, but browser Authorization Code with PKCE and production issuer/role selection are absent | Users must supply an access token or use the local-only development identity; production sign-in is not ready | High | Partial |
| TD-008 | Responses are not cached and rate limits are process-local | Repeated requests can consume NASA quota; limits do not coordinate across replicas | Medium | Open |
| TD-009 | Saved-record CRUD, compare, report listing/read/delete, settings/session, and admin source/job routes are implemented; provider-backed report/conversation generation is unavailable and E2E flows remain unverified | Assistant/report generation remains unavailable; local user-workspace is testable | High | Partial |
| TD-010 | The `13d429c` GitHub Actions Python job found invalid syntax after generated-migration whitespace cleanup; migration has been restored and local Python checks pass, with corrected main-branch run pending | Remote runner verification is still needed | Medium | Open |
| TD-011 | Monitoring, encrypted backup, restore exercise, image scanning, and resource limits are not configured | Operational recovery/security posture is incomplete | High | Open |
| TD-012 | Authenticated MCP server, ten tools, resources, templates, and prompts are implemented and smoke-tested locally; MCP Inspector and production OIDC configuration remain | Local MCP acceptance is implemented; production evidence remains | High | Open |
| OD-001 | NASA AI/SI wording and attribution for generated NASA-derived content need formal review | AI generation must remain disabled until resolved | High | Release gate |
| OD-002 | Production identity issuer and account policy are undecided | Protected public features cannot be released | Medium | Open |
| OD-003 | Map tile provider usage terms need review | Public Earth-event map usage is not cleared | Medium | Open |

See [implementation progress](docs/IMPLEMENTATION_PROGRESS.md) for current test evidence and [the implementation backlog](docs/10-implementation/TASK_BACKLOG.md) for planned acceptance criteria.
