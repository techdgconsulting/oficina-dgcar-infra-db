import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "cleanup", Path(__file__).resolve().parents[1] / "aws" / "purge_rds_backups.py")
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class RdsBackupCleanupTests(unittest.TestCase):
    def test_invalid_scope_or_confirmation_never_calls_aws(self):
        with patch.object(cleanup, "aws") as api:
            for environment, confirm in (("dev", "DESTROY"), ("prod", "")):
                with self.assertRaises(ValueError):
                    cleanup.purge(environment, confirm)
            api.assert_not_called()

    def test_existing_database_blocks_backup_deletion(self):
        with patch.object(cleanup, "aws", return_value={"DBInstances": [
            {"DBInstanceIdentifier": "oficina-dgcar-prod-postgres"}]}) as api:
            with self.assertRaises(ValueError):
                cleanup.purge("prod", "DESTROY")
            self.assertEqual(api.call_count, 1)

    def test_inventory_matches_exact_database_not_prefix(self):
        with patch.object(cleanup, "aws", side_effect=[{"DBSnapshots": [
            {"DBInstanceIdentifier": "oficina-dgcar-prod-postgres", "DBSnapshotIdentifier": "owned"},
            {"DBInstanceIdentifier": "oficina-dgcar-homolog-postgres", "DBSnapshotIdentifier": "other"},
            {"DBInstanceIdentifier": "oficina-dgcar-prod-postgres-copy", "DBSnapshotIdentifier": "copy"},
        ]}, {"DBInstanceAutomatedBackups": []}]):
            snapshots, _ = cleanup.inventory("oficina-dgcar-prod-postgres")
            self.assertEqual([s["DBSnapshotIdentifier"] for s in snapshots], ["owned"])

    def test_each_environment_deletes_only_its_inventory_and_verifies(self):
        for environment in ("homolog", "prod"):
            snapshots = [{"DBSnapshotIdentifier": "snapshot", "Status": "available"}]
            backups = [{"DbiResourceId": "db-owned"}]
            with self.subTest(environment=environment), patch.object(cleanup, "aws", return_value={"DBInstances": []}) as api, patch.object(cleanup, "inventory", side_effect=[(snapshots, backups), ([], [])]) as inventory:
                cleanup.purge(environment, "DESTROY")
                self.assertEqual(inventory.call_args.args, (f"oficina-dgcar-{environment}-postgres",))
                self.assertIn(unittest.mock.call("delete-db-snapshot", "--db-snapshot-identifier", "snapshot"), api.call_args_list)
                self.assertIn(unittest.mock.call("delete-db-instance-automated-backup", "--dbi-resource-id", "db-owned"), api.call_args_list)

    def test_already_empty_cleanup_is_idempotent(self):
        with patch.object(cleanup, "aws", return_value={"DBInstances": []}) as api, patch.object(cleanup, "inventory", return_value=([], [])):
            cleanup.purge("homolog", "DESTROY")
            self.assertEqual(api.call_count, 1)

    def test_incomplete_inventory_blocks_all_deletions(self):
        with patch.object(cleanup, "aws", return_value={"DBInstances": []}) as api, patch.object(cleanup, "inventory", return_value=([{"DBSnapshotIdentifier": "ok"}], [{}])):
            with self.assertRaises(ValueError):
                cleanup.purge("prod", "DESTROY")
            self.assertEqual(api.call_count, 1)

    def test_api_failure_is_not_reported_as_empty(self):
        with patch.object(cleanup, "aws", return_value={"DBInstances": []}), patch.object(cleanup, "inventory", side_effect=RuntimeError("Denied")):
            with self.assertRaises(RuntimeError):
                cleanup.purge("prod", "DESTROY")

    def test_cleanup_timeout_keeps_teardown_failed(self):
        with patch.object(cleanup, "aws", return_value={"DBInstances": []}), patch.object(cleanup, "inventory", side_effect=[([], [])] + [([], [{"DbiResourceId": "remaining"}])] * 60), patch.object(cleanup.time, "sleep"):
            with self.assertRaises(RuntimeError):
                cleanup.purge("prod", "DESTROY")
