"""Unit tests for the safe custom-claims backfill mode."""

from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from scripts.migration.backfill_custom_claims import (
    backfill_custom_claims,
    claims_from_user_document,
)


class FakeUsersCollection:
    def __init__(self, documents):
        self.documents = documents

    def stream(self):
        return iter(self.documents)


class FakeDatabase:
    def __init__(self, documents):
        self.users = FakeUsersCollection(documents)

    def collection(self, name):
        assert name == "users"
        return self.users


def test_claims_are_derived_from_firestore_user_fields():
    assert claims_from_user_document(
        {"role": "partner", "tenant_id": "tenant-1", "entity_id": "p-1"}
    ) == {
        "role": "partner",
        "tenant": "tenant-1",
        "entity_id": "p-1",
    }


def test_dry_run_counts_users_without_writing_claims():
    documents = [
        SimpleNamespace(
            id="firebase-user-123",
            to_dict=lambda: {
                "role": "student",
                "tenant_id": "tenant-1",
                "entity_id": "s-1",
            },
        ),
        SimpleNamespace(
            id="firebase-user-456",
            to_dict=lambda: {"role": "unknown", "tenant_id": "tenant-1"},
        ),
    ]
    output = StringIO()

    with patch(
        "scripts.migration.backfill_custom_claims.auth.set_custom_user_claims"
    ) as set_claims:
        counts = backfill_custom_claims(
            FakeDatabase(documents), apply=False, output=output
        )

    assert counts == {"total": 2, "eligible": 1, "skipped": 1, "written": 0}
    set_claims.assert_not_called()
    assert "firebase-user-123" not in output.getvalue()
    assert "dry-run" in output.getvalue()
