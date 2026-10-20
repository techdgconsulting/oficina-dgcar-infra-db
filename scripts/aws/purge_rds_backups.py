"""Remove only the selected DGCar database's backups after its confirmed destroy."""
import argparse
import json
import subprocess
import time


def aws(*args):
    result = subprocess.run(
        ["aws", "rds", *args, "--output", "json"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"RDS operation failed: {args[0]}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def inventory(identifier):
    snapshots = aws("describe-db-snapshots", "--snapshot-type", "manual")["DBSnapshots"]
    backups = aws("describe-db-instance-automated-backups")["DBInstanceAutomatedBackups"]
    return (
        [s for s in snapshots if s.get("DBInstanceIdentifier") == identifier],
        [b for b in backups if b.get("DBInstanceIdentifier") == identifier],
    )


def purge(environment, confirm):
    if environment not in ("homolog", "prod") or confirm != "DESTROY":
        raise ValueError("Select homolog/prod and confirm DESTROY.")
    identifier = f"oficina-dgcar-{environment}-postgres"
    instances = aws("describe-db-instances")["DBInstances"]
    if any(db.get("DBInstanceIdentifier") == identifier for db in instances):
        raise ValueError("Database still exists; backup removal requires completed destroy.")

    snapshots, backups = inventory(identifier)
    # Validate every deletion identifier before making the first mutation.
    if any(not s.get("DBSnapshotIdentifier") for s in snapshots):
        raise ValueError("Snapshot identifier missing.")
    if any(not b.get("DbiResourceId") for b in backups):
        raise ValueError("Automated backup resource identifier missing.")
    for snapshot in snapshots:
        name = snapshot["DBSnapshotIdentifier"]
        status = snapshot.get("Status")
        if status != "deleting":
            if status != "available":
                aws("wait", "db-snapshot-available", "--db-snapshot-identifier", name)
            aws("delete-db-snapshot", "--db-snapshot-identifier", name)
        aws("wait", "db-snapshot-deleted", "--db-snapshot-identifier", name)
    for backup in backups:
        aws("delete-db-instance-automated-backup", "--dbi-resource-id", backup["DbiResourceId"])
    for attempt in range(60):
        remaining_snapshots, remaining_backups = inventory(identifier)
        if not remaining_snapshots and not remaining_backups:
            print(f"{identifier}: no manual snapshots or retained automated backups remain.")
            return
        if attempt < 59:
            time.sleep(10)
    raise RuntimeError("Backup removal did not complete; environment teardown remains incomplete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", choices=("homolog", "prod"), required=True)
    parser.add_argument("--confirm", choices=("DESTROY",), required=True)
    options = parser.parse_args()
    purge(options.environment, options.confirm)
