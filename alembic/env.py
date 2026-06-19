from logging.config import fileConfig
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from alembic import context

import os
import sys
# Ensure the app directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables first
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from app.db.models.base_model import BaseModel
    from app.db.models.analytics import AnalyticsEvent
    from app.config import settings
except ImportError as e:
    print(f"Warning: Failed to import models: {e}")
    BaseModel = None
    AnalyticsEvent = None
    settings = None

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the database URL, fallback to ini file if settings are missing
db_url = None
if settings and hasattr(settings, 'DATABASE_URL_SYNC'):
    db_url = settings.DATABASE_URL_SYNC
else:
    db_url = config.get_main_option("sqlalchemy.url")
config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Combine metadata from both declarative bases
target_metadata = None
if BaseModel and AnalyticsEvent:
    # Combine both metadata objects
    target_metadata = BaseModel.metadata
    for table in AnalyticsEvent.metadata.tables.values():
        if table.name not in target_metadata.tables:
            target_metadata.tables[table.name] = table
elif BaseModel:
    target_metadata = BaseModel.metadata
elif AnalyticsEvent:
    target_metadata = AnalyticsEvent.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(config.get_main_option("sqlalchemy.url"))
    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
