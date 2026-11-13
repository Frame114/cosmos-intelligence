# Environment Configuration

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 configuration contract  
**Purpose:** Specify the intended Environment Configuration requirements and implementation constraints.  
**Scope:** Covers the proposed Environment Configuration behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Nonsecret settings

APP_ENV, APP_NAME, LOG_LEVEL, PUBLIC_BASE_URL, CORS_ALLOWED_ORIGINS (development only), NASA_API_TIMEOUT_SECONDS, NASA_MAX_CONCURRENCY, DATABASE_HOST/PORT/NAME/USER, DB_POOL_SIZE, OIDC_ISSUER_URL, OIDC_AUDIENCE, OIDC_CLIENT_ID, OPENROUTER_MODEL, OPENROUTER_ENABLED, AI_MAX_OUTPUT_TOKENS, rate limits, cache TTLs, and retention periods.

## Secret file settings

NASA_API_KEY_FILE, OPENROUTER_API_KEY_FILE, DATABASE_PASSWORD_FILE, POSTGRES_PASSWORD_FILE, OIDC_CLIENT_SECRET_FILE when applicable, and BACKUP_ENCRYPTION_KEY_FILE. Application settings load file contents into SecretStr and must not echo them during validation.

## Environment rules

Development loads ignored .env and local Compose secret files. Test uses fake credentials and mocked upstreams. Production requires HTTPS, configured OIDC, strong unique DB password, production secret files, known public origin, restrictive CORS, and debug/docs flags disabled. AI is disabled by default until model configuration, spend limits, and NASA content policy approval are complete. Never silently use DEMO_KEY in a public deployment.

## Related documents

[Secrets Management](../06-security/SECRETS_MANAGEMENT.md), [Docker Compose Specification](DOCKER_COMPOSE_SPECIFICATION.md), [Local Development](../11-operations/LOCAL_DEVELOPMENT.md).
