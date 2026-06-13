#!/bin/bash
# Back up the VetAnesthesia database to a timestamped file.
# Usage:  bash scripts/backup.sh [destination_folder]
# Example: bash scripts/backup.sh /Volumes/USB

cd "$(dirname "$0")/.."

DEST="${1:-.}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="vetanesthesia_backup_${TIMESTAMP}.db"

# Support both manual install (anesthesia.db in app root) and Docker (data/)
if [ -f "data/anesthesia.db" ]; then
  DB="data/anesthesia.db"
elif [ -f "anesthesia.db" ]; then
  DB="anesthesia.db"
else
  echo "ERROR: Database file not found."
  exit 1
fi

cp "$DB" "${DEST}/${FILENAME}"
echo "Backup saved: ${DEST}/${FILENAME}"
