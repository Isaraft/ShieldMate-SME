from alembic import context

from app import models  # noqa: F401
from app.config import Settings
from app.db import Base, Database

target_metadata = Base.metadata
settings = Settings()


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    database = Database(settings.database_url)
    try:
        with database.engine.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata, render_as_batch=True
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        database.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
