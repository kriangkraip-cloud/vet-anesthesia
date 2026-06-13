#!/bin/bash
# Restore the VetAnesthesia database from a backup file.
# Usage:  bash scripts/restore.sh /path/to/vetanesthesia_backup_YYYYMMDD.db
# IMPORTANT: Stop the server before restoring.

cd "$(dirname "$0")/.."

BACKUP="$1"
if [ -z "$BACKUP" ] || [ ! -f "$BACKUP" ]; then
  echo "Usage: bash scripts/restore.sh /path/to/backup.db"
  exit 1
fi

# Detect database location
if [ -d "data" ]; then
  DB="data/anesthesia.db"
else
  DB="anesthesia.db"
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -f "$DB" ]; then
  cp "$DB" "${DB}.pre_restore_${TIMESTAMP}"
  echo "Current database backed up to: ${DB}.pre_restore_${TIMESTAMP}"
fi

cp "$BACKUP" "$DB"
echo "Database restored from: $BACKUP"
echo "Restart the server to apply changes."
