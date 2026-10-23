from collections.abc import Iterator
from pathlib import Path

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    """Future models share this migration-managed metadata; no business tables yet."""


class Database:
    def __init__(self, url: str) -> None:
        database = make_url(url).database
        if database and database != ":memory:":
            Path(database).parent.mkdir(parents=True, exist_ok=True)
        options = {"poolclass": StaticPool} if database == ":memory:" else {}
        self.engine = create_engine(
            url, connect_args={"check_same_thread": False, "timeout": 5}, **options
        )

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection: object, _: object) -> None:
            # SQLAlchemy's DBAPI event is dynamically typed; narrow locally.
            from sqlite3 import Connection

            if isinstance(connection, Connection):
                connection.execute("PRAGMA foreign_keys=ON")

        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    def close(self) -> None:
        self.engine.dispose()


def get_session(request: Request) -> Iterator[Session]:
    """Future routes explicitly commit writes; uncommitted work is rolled back on close."""
    database: Database = request.app.state.database
    with database.sessions() as session:
        yield session
