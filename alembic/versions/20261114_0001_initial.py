"""Create initial scientific and application data schema.

Revision ID: 20261114_0001
Revises: None
Create Date: 2026-11-14

This first migration is frozen PostgreSQL DDL generated from the initial model
metadata. Future schema changes must use new, explicit Alembic revisions.
"""

from alembic import op

revision = "20261114_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE user_account (
	id UUID NOT NULL,
	oidc_subject VARCHAR(255) NOT NULL,
	role VARCHAR(40) DEFAULT 'user' NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	last_seen_at TIMESTAMP WITH TIME ZONE,
	CONSTRAINT pk_user_account PRIMARY KEY (id),
	CONSTRAINT uq_user_account_oidc_subject UNIQUE (oidc_subject)
)""")

    op.execute("""CREATE TABLE prompt_version (
	id UUID NOT NULL,
	name VARCHAR(120) NOT NULL,
	version VARCHAR(80) NOT NULL,
	system_template TEXT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	checksum VARCHAR(64) NOT NULL,
	active BOOLEAN DEFAULT 'false' NOT NULL,
	CONSTRAINT pk_prompt_version PRIMARY KEY (id),
	CONSTRAINT uq_prompt_version_name_version UNIQUE (name, version)
)""")

    op.execute("""CREATE TABLE audit_event (
	id UUID NOT NULL,
	actor_subject VARCHAR(255),
	action VARCHAR(120) NOT NULL,
	target_type VARCHAR(80) NOT NULL,
	target_id VARCHAR(255),
	request_id VARCHAR(128),
	details JSONB DEFAULT '{}' NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_audit_event PRIMARY KEY (id)
)""")

    op.execute("""CREATE INDEX ix_audit_event_created ON audit_event (created_at)""")

    op.execute("""CREATE TABLE data_source (
	code VARCHAR(40) NOT NULL,
	display_name VARCHAR(120) NOT NULL,
	base_host VARCHAR(255) NOT NULL,
	enabled BOOLEAN DEFAULT 'true' NOT NULL,
	policy JSONB DEFAULT '{}' NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_data_source PRIMARY KEY (code)
)""")

    op.execute("""CREATE TABLE research_conversation (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	title VARCHAR(255),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	CONSTRAINT pk_research_conversation PRIMARY KEY (id),
	CONSTRAINT fk_research_conversation_user_id_user_account FOREIGN KEY(user_id) REFERENCES user_account (id) ON DELETE CASCADE
)""")

    op.execute(
        """CREATE INDEX ix_research_conversation_user_updated ON research_conversation (user_id, updated_at)"""
    )

    op.execute("""CREATE TABLE ai_report (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	prompt_version_id UUID NOT NULL,
	title VARCHAR(255) NOT NULL,
	question TEXT NOT NULL,
	structured_answer JSONB NOT NULL,
	model_id VARCHAR(255) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	deleted_at TIMESTAMP WITH TIME ZONE,
	CONSTRAINT pk_ai_report PRIMARY KEY (id),
	CONSTRAINT fk_ai_report_user_id_user_account FOREIGN KEY(user_id) REFERENCES user_account (id) ON DELETE CASCADE,
	CONSTRAINT fk_ai_report_prompt_version_id_prompt_version FOREIGN KEY(prompt_version_id) REFERENCES prompt_version (id) ON DELETE RESTRICT
)""")

    op.execute("""CREATE INDEX ix_ai_report_user_created ON ai_report (user_id, created_at)""")

    op.execute("""CREATE TABLE ingestion_job (
	id UUID NOT NULL,
	source_code VARCHAR(40) NOT NULL,
	job_type VARCHAR(80) NOT NULL,
	window_start DATE,
	window_end DATE,
	state VARCHAR(20) DEFAULT 'queued' NOT NULL,
	attempts INTEGER DEFAULT '0' NOT NULL,
	next_run_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	lease_until TIMESTAMP WITH TIME ZONE,
	locked_by VARCHAR(120),
	started_at TIMESTAMP WITH TIME ZONE,
	finished_at TIMESTAMP WITH TIME ZONE,
	counts JSONB DEFAULT '{}' NOT NULL,
	safe_error_code VARCHAR(80),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_ingestion_job PRIMARY KEY (id),
	CONSTRAINT ck_ingestion_job_state_allowed CHECK (state IN ('queued', 'running', 'succeeded', 'failed')),
	CONSTRAINT ck_ingestion_job_attempts_nonnegative CHECK (attempts >= 0),
	CONSTRAINT fk_ingestion_job_source_code_data_source FOREIGN KEY(source_code) REFERENCES data_source (code) ON DELETE RESTRICT
)""")

    op.execute("""CREATE INDEX ix_ingestion_job_due ON ingestion_job (state, next_run_at)""")

    op.execute("""CREATE TABLE api_request_log (
	id UUID NOT NULL,
	source_code VARCHAR(40),
	operation VARCHAR(120) NOT NULL,
	started_at TIMESTAMP WITH TIME ZONE NOT NULL,
	duration_ms INTEGER NOT NULL,
	status_code SMALLINT,
	outcome VARCHAR(40) NOT NULL,
	retry_count INTEGER DEFAULT '0' NOT NULL,
	rate_limit_remaining INTEGER,
	request_id VARCHAR(128),
	safe_error_code VARCHAR(80),
	CONSTRAINT pk_api_request_log PRIMARY KEY (id),
	CONSTRAINT ck_api_request_log_duration_nonnegative CHECK (duration_ms >= 0),
	CONSTRAINT ck_api_request_log_retry_count_nonnegative CHECK (retry_count >= 0),
	CONSTRAINT fk_api_request_log_source_code_data_source FOREIGN KEY(source_code) REFERENCES data_source (code) ON DELETE SET NULL
)""")

    op.execute(
        """CREATE INDEX ix_api_request_log_source_started ON api_request_log (source_code, started_at)"""
    )

    op.execute("""CREATE INDEX ix_api_request_log_started ON api_request_log (started_at)""")

    op.execute("""CREATE TABLE source_record (
	id UUID NOT NULL,
	source_code VARCHAR(40) NOT NULL,
	external_id VARCHAR(255) NOT NULL,
	source_url TEXT,
	retrieved_at TIMESTAMP WITH TIME ZONE NOT NULL,
	source_updated_at TIMESTAMP WITH TIME ZONE,
	payload_hash CHAR(64) NOT NULL,
	raw_payload JSONB NOT NULL,
	schema_version VARCHAR(80) NOT NULL,
	normalizer_version VARCHAR(80) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_source_record PRIMARY KEY (id),
	CONSTRAINT uq_source_record_identity UNIQUE (source_code, external_id),
	CONSTRAINT fk_source_record_source_code_data_source FOREIGN KEY(source_code) REFERENCES data_source (code) ON DELETE RESTRICT
)""")

    op.execute(
        """CREATE INDEX ix_source_record_source_retrieved ON source_record (source_code, retrieved_at)"""
    )

    op.execute("""CREATE TABLE saved_record (
	id UUID NOT NULL,
	user_id UUID NOT NULL,
	source_record_id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_saved_record PRIMARY KEY (id),
	CONSTRAINT uq_saved_record_user_source UNIQUE (user_id, source_record_id),
	CONSTRAINT fk_saved_record_user_id_user_account FOREIGN KEY(user_id) REFERENCES user_account (id) ON DELETE CASCADE,
	CONSTRAINT fk_saved_record_source_record_id_source_record FOREIGN KEY(source_record_id) REFERENCES source_record (id) ON DELETE CASCADE
)""")

    op.execute(
        """CREATE INDEX ix_saved_record_user_created ON saved_record (user_id, created_at)"""
    )

    op.execute("""CREATE TABLE research_message (
	id UUID NOT NULL,
	conversation_id UUID NOT NULL,
	role VARCHAR(20) NOT NULL,
	content TEXT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	prompt_version_id UUID,
	model_id VARCHAR(255),
	usage JSONB,
	status VARCHAR(32) DEFAULT 'complete' NOT NULL,
	CONSTRAINT pk_research_message PRIMARY KEY (id),
	CONSTRAINT ck_research_message_role_allowed CHECK (role IN ('user', 'assistant', 'system')),
	CONSTRAINT fk_research_message_conversation_id_research_conversation FOREIGN KEY(conversation_id) REFERENCES research_conversation (id) ON DELETE CASCADE,
	CONSTRAINT fk_research_message_prompt_version_id_prompt_version FOREIGN KEY(prompt_version_id) REFERENCES prompt_version (id) ON DELETE SET NULL
)""")

    op.execute(
        """CREATE INDEX ix_research_message_conversation_created ON research_message (conversation_id, created_at)"""
    )

    op.execute("""CREATE TABLE report_evidence (
	report_id UUID NOT NULL,
	source_record_id UUID NOT NULL,
	citation_key VARCHAR(80) NOT NULL,
	excerpt_hash VARCHAR(64),
	rank INTEGER NOT NULL,
	CONSTRAINT pk_report_evidence PRIMARY KEY (report_id, source_record_id),
	CONSTRAINT uq_report_evidence_citation UNIQUE (report_id, citation_key),
	CONSTRAINT fk_report_evidence_report_id_ai_report FOREIGN KEY(report_id) REFERENCES ai_report (id) ON DELETE CASCADE,
	CONSTRAINT fk_report_evidence_source_record_id_source_record FOREIGN KEY(source_record_id) REFERENCES source_record (id) ON DELETE RESTRICT
)""")

    op.execute("""CREATE INDEX ix_report_evidence_source ON report_evidence (source_record_id)""")

    op.execute("""CREATE TABLE apod_record (
	source_record_id UUID NOT NULL,
	apod_date DATE NOT NULL,
	title TEXT NOT NULL,
	explanation TEXT NOT NULL,
	media_type VARCHAR(20) NOT NULL,
	page_url TEXT NOT NULL,
	media_url TEXT,
	hd_url TEXT,
	alt_text TEXT,
	credit TEXT,
	copyright TEXT,
	CONSTRAINT pk_apod_record PRIMARY KEY (source_record_id),
	CONSTRAINT ck_apod_record_media_type_allowed CHECK (media_type IN ('image', 'video', 'iframe')),
	CONSTRAINT fk_apod_record_source_record_id_source_record FOREIGN KEY(source_record_id) REFERENCES source_record (id) ON DELETE CASCADE,
	CONSTRAINT uq_apod_record_apod_date UNIQUE (apod_date)
)""")

    op.execute("""CREATE INDEX ix_apod_record_date_desc ON apod_record (apod_date)""")

    op.execute("""CREATE TABLE neo_object (
	source_record_id UUID NOT NULL,
	neo_id VARCHAR(32) NOT NULL,
	name TEXT NOT NULL,
	absolute_magnitude NUMERIC(12, 5),
	diameter_min_km NUMERIC(18, 9),
	diameter_max_km NUMERIC(18, 9),
	potentially_hazardous BOOLEAN,
	sentry_object BOOLEAN,
	jpl_url TEXT,
	CONSTRAINT pk_neo_object PRIMARY KEY (source_record_id),
	CONSTRAINT ck_neo_object_diameter_ordered CHECK (diameter_min_km IS NULL OR diameter_max_km IS NULL OR diameter_min_km <= diameter_max_km),
	CONSTRAINT uq_neo_object_neo_id UNIQUE (neo_id),
	CONSTRAINT fk_neo_object_source_record_id_source_record FOREIGN KEY(source_record_id) REFERENCES source_record (id) ON DELETE CASCADE
)""")

    op.execute("""CREATE INDEX ix_neo_object_name ON neo_object (name)""")

    op.execute("""CREATE TABLE space_weather_event (
	source_record_id UUID NOT NULL,
	event_type VARCHAR(40) NOT NULL,
	activity_id VARCHAR(255),
	start_time TIMESTAMP WITH TIME ZONE,
	end_time TIMESTAMP WITH TIME ZONE,
	class_type VARCHAR(80),
	source_location VARCHAR(255),
	details JSONB NOT NULL,
	link TEXT,
	CONSTRAINT pk_space_weather_event PRIMARY KEY (source_record_id),
	CONSTRAINT fk_space_weather_event_source_record_id_source_record FOREIGN KEY(source_record_id) REFERENCES source_record (id) ON DELETE CASCADE
)""")

    op.execute(
        """CREATE INDEX ix_space_weather_type_start ON space_weather_event (event_type, start_time)"""
    )

    op.execute("""CREATE TABLE earth_event (
	source_record_id UUID NOT NULL,
	eonet_id VARCHAR(255) NOT NULL,
	title TEXT NOT NULL,
	description TEXT,
	opened_at TIMESTAMP WITH TIME ZONE,
	closed_at TIMESTAMP WITH TIME ZONE,
	categories JSONB NOT NULL,
	sources JSONB NOT NULL,
	geometry JSONB,
	geometry_type VARCHAR(40),
	magnitude_value NUMERIC(20, 6),
	magnitude_unit VARCHAR(80),
	CONSTRAINT pk_earth_event PRIMARY KEY (source_record_id),
	CONSTRAINT fk_earth_event_source_record_id_source_record FOREIGN KEY(source_record_id) REFERENCES source_record (id) ON DELETE CASCADE,
	CONSTRAINT uq_earth_event_eonet_id UNIQUE (eonet_id)
)""")

    op.execute(
        """CREATE INDEX ix_earth_event_closed_opened ON earth_event (closed_at, opened_at)"""
    )

    op.execute("""CREATE TABLE media_record (
	source_record_id UUID NOT NULL,
	nasa_id VARCHAR(255) NOT NULL,
	title TEXT NOT NULL,
	media_type VARCHAR(24) NOT NULL,
	date_created TIMESTAMP WITH TIME ZONE,
	description TEXT,
	description_508 TEXT,
	keywords JSONB NOT NULL,
	creators JSONB NOT NULL,
	asset_manifest_url TEXT NOT NULL,
	detail_url TEXT NOT NULL,
	rights_note TEXT,
	CONSTRAINT pk_media_record PRIMARY KEY (source_record_id),
	CONSTRAINT fk_media_record_source_record_id_source_record FOREIGN KEY(source_record_id) REFERENCES source_record (id) ON DELETE CASCADE,
	CONSTRAINT uq_media_record_nasa_id UNIQUE (nasa_id)
)""")

    op.execute(
        """CREATE INDEX ix_media_record_type_created ON media_record (media_type, date_created)"""
    )

    op.execute("""CREATE TABLE neo_approach (
	id UUID NOT NULL,
	source_record_id UUID NOT NULL,
	neo_id VARCHAR(32) NOT NULL,
	approach_date DATE NOT NULL,
	epoch_date_close TIMESTAMP WITH TIME ZONE,
	velocity_km_s NUMERIC(20, 9),
	miss_distance_km NUMERIC(30, 6),
	miss_distance_au NUMERIC(24, 12),
	orbiting_body VARCHAR(80),
	CONSTRAINT pk_neo_approach PRIMARY KEY (id),
	CONSTRAINT uq_neo_approach_identity UNIQUE (neo_id, approach_date, orbiting_body),
	CONSTRAINT ck_neo_approach_velocity_nonnegative CHECK (velocity_km_s IS NULL OR velocity_km_s >= 0),
	CONSTRAINT ck_neo_approach_distance_nonnegative CHECK (miss_distance_km IS NULL OR miss_distance_km >= 0),
	CONSTRAINT fk_neo_approach_source_record_id_source_record FOREIGN KEY(source_record_id) REFERENCES source_record (id) ON DELETE CASCADE,
	CONSTRAINT fk_neo_approach_neo_id_neo_object FOREIGN KEY(neo_id) REFERENCES neo_object (neo_id) ON DELETE CASCADE
)""")

    op.execute("""CREATE INDEX ix_neo_approach_date ON neo_approach (approach_date)""")


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS "neo_approach" CASCADE')
    op.execute('DROP TABLE IF EXISTS "space_weather_event" CASCADE')
    op.execute('DROP TABLE IF EXISTS "saved_record" CASCADE')
    op.execute('DROP TABLE IF EXISTS "research_message" CASCADE')
    op.execute('DROP TABLE IF EXISTS "report_evidence" CASCADE')
    op.execute('DROP TABLE IF EXISTS "neo_object" CASCADE')
    op.execute('DROP TABLE IF EXISTS "media_record" CASCADE')
    op.execute('DROP TABLE IF EXISTS "earth_event" CASCADE')
    op.execute('DROP TABLE IF EXISTS "apod_record" CASCADE')
    op.execute('DROP TABLE IF EXISTS "source_record" CASCADE')
    op.execute('DROP TABLE IF EXISTS "research_conversation" CASCADE')
    op.execute('DROP TABLE IF EXISTS "ingestion_job" CASCADE')
    op.execute('DROP TABLE IF EXISTS "api_request_log" CASCADE')
    op.execute('DROP TABLE IF EXISTS "ai_report" CASCADE')
    op.execute('DROP TABLE IF EXISTS "user_account" CASCADE')
    op.execute('DROP TABLE IF EXISTS "prompt_version" CASCADE')
    op.execute('DROP TABLE IF EXISTS "data_source" CASCADE')
    op.execute('DROP TABLE IF EXISTS "audit_event" CASCADE')
