#!/usr/bin/env python3
"""Backfill Firebase custom claims from the Firestore users collection.

Dry-run is the default.  Use ``--apply`` only after reviewing the count and
confirming the target project explicitly.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parents[2]))

from firebase_admin import auth

VALID_ROLES = {"admin", "employee", "student", "partner"}


def _short_uid(uid: str) -> str:
    if len(uid) <= 8:
        return "***"
    return f"{uid[:4]}...{uid[-2:]}"


def claims_from_user_document(data: dict[str, Any]) -> dict[str, str] | None:
    """Build the supported claims or return None for an incomplete document."""
    role = data.get("role")
    tenant = data.get("tenant") or data.get("tenant_id")
    entity_id = data.get("entity_id")

    if role not in VALID_ROLES or not isinstance(tenant, str) or not tenant:
        return None
    if entity_id is not None and not isinstance(entity_id, str):
        entity_id = str(entity_id)

    claims = {"role": role, "tenant": tenant}
    if entity_id:
        claims["entity_id"] = entity_id
    return claims


def backfill_custom_claims(
    database: Any, *, apply: bool = False, output: Any = None
) -> dict[str, int]:
    """Plan or apply claims for every document in ``users``.

    ``database`` is injected so the dry-run can be tested without a live
    Firebase project.  The function never prints sensitive fields in full.
    """
    output = output or sys.stdout
    counts = Counter(total=0, eligible=0, skipped=0, written=0)

    for document in database.collection("users").stream():
        counts["total"] += 1
        claims = claims_from_user_document(document.to_dict() or {})
        if claims is None:
            counts["skipped"] += 1
            continue

        counts["eligible"] += 1
        if apply:
            auth.set_custom_user_claims(document.id, claims)
            counts["written"] += 1
        else:
            print(
                f"dry-run: claims prontas para {_short_uid(document.id)}",
                file=output,
            )

    return dict(counts)


def main() -> int:
    from src.auth import initialize_firebase
    from src.config import FIRESTORE_PROJECT
    from src.db.firestore import get_database

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write claims; without this flag the script only performs a dry-run",
    )
    args = parser.parse_args()

    initialize_firebase()
    database = get_database()
    counts = backfill_custom_claims(database, apply=args.apply)
    mode = "apply" if args.apply else "dry-run"
    print(
        f"{mode}: project={FIRESTORE_PROJECT} total={counts['total']} "
        f"eligible={counts['eligible']} skipped={counts['skipped']} "
        f"written={counts['written']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
