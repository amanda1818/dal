# Copy to .env and fill in as needed. All optional for local running.

# Storage. Default is a local SQLite file. For production use PostgreSQL:
# DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/dal

# Optional — enables the AI classification pass. Without it, the engine runs rules-only.
# ANTHROPIC_API_KEY=sk-ant-...
# CLASSIFY_MODEL=claude-sonnet-4-20250514

# Engine thresholds (defaults shown)
# IDLE_THRESHOLD_MIN=10
# CONFIDENCE_REVIEW_THRESHOLD=0.6
# STANDARD_TIME_PERCENTILE=25
# PEER_OUTLIER_MULTIPLE=2.0
