"""Explicit local-only maintenance entry; no HTTP mutation accepts fabricated observations."""

import argparse
from uuid import UUID

from app.config import Settings
from app.db import Database
from app.findings.reconcile import reconcile_pending


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate retained terminal scans offline, policy v1"
    )
    parser.add_argument("--organization-id", required=True, type=UUID)
    args = parser.parse_args()
    settings = Settings()
    database = Database(settings.database_url)
    total = 0
    try:
        while count := reconcile_pending(database, str(args.organization_id), limit=100):
            total += count
        print(f"Evaluated {total} terminal scans; no network requests performed.")
    finally:
        database.close()


if __name__ == "__main__":
    main()
