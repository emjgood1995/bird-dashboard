#!/usr/bin/env bash
set -euo pipefail

# Sync a BirdNET-Pi SQLite database into this repo's LFS file and push.
#
# Usage:
#   scripts/birdmic_sync_to_repo.sh [SOURCE_DB]
#
# If SOURCE_DB is not provided, the script tries common BirdNET-Pi locations.
#
# Optional env vars:
#   REPO_DIR     (default: parent directory of this script)
#   TARGET_FILE  (default: birds_lfs.db)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${REPO_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
TARGET_FILE="${TARGET_FILE:-birds_lfs.db}"

SOURCE_DB="${1:-}"

if [[ -z "${SOURCE_DB}" ]]; then
  CANDIDATES=(
    "/home/birdmic/BirdNET-Pi/scripts/birds.db"
    "/home/birdnet/BirdNET-Pi/scripts/birds.db"
    "/home/birdmic/BirdNET-Pi/birds.db"
    "/home/birdnet/BirdNET-Pi/birds.db"
    "/home/pi/BirdNET-Pi/scripts/birds.db"
    "/home/pi/BirdNET-Pi/birds.db"
  )
  for p in "${CANDIDATES[@]}"; do
    if [[ -f "${p}" ]]; then
      SOURCE_DB="${p}"
      break
    fi
  done
fi

if [[ -z "${SOURCE_DB}" ]]; then
  echo "ERROR: could not detect SOURCE_DB."
  echo "Pass it explicitly, e.g.:"
  echo "  $0 /home/birdmic/BirdNET-Pi/scripts/birds.db"
  exit 1
fi

if [[ ! -f "${SOURCE_DB}" ]]; then
  echo "ERROR: source db not found: ${SOURCE_DB}"
  exit 1
fi

echo "Using source DB: ${SOURCE_DB}"
echo "Repo dir: ${REPO_DIR}"
echo "Target file: ${TARGET_FILE}"

"${REPO_DIR}/scripts/push_birds_db.sh" "${SOURCE_DB}"
