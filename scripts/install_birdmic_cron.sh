#!/usr/bin/env bash
set -euo pipefail

# Install/update cron jobs for:
# 1) database sync -> git push
# 2) BirdSongs WAV cleanup
#
# Usage:
#   scripts/install_birdmic_cron.sh /absolute/path/to/source.db
#
# Optional env vars:
#   REPO_DIR           (default: parent directory of this script)
#   SYNC_SCHEDULE      (default: "15 2 * * *")
#   CLEAN_SCHEDULE     (default: "45 2 * * *")
#   CLEAN_DAYS         (default: 14)
#   BIRDSONGS_DIR      (default: /home/birdnet/BirdNET-Pi/BirdSongs)
#   LOG_DIR            (default: $REPO_DIR/logs)

SOURCE_DB="${1:-}"
if [[ -z "${SOURCE_DB}" ]]; then
  echo "ERROR: missing source db path."
  echo "Usage: $0 /absolute/path/to/source.db"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${REPO_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
SYNC_SCHEDULE="${SYNC_SCHEDULE:-15 2 * * *}"
CLEAN_SCHEDULE="${CLEAN_SCHEDULE:-45 2 * * *}"
CLEAN_DAYS="${CLEAN_DAYS:-14}"
BIRDSONGS_DIR="${BIRDSONGS_DIR:-/home/birdnet/BirdNET-Pi/BirdSongs}"
LOG_DIR="${LOG_DIR:-${REPO_DIR}/logs}"

mkdir -p "${LOG_DIR}"

SYNC_CMD="cd ${REPO_DIR} && ${REPO_DIR}/scripts/birdmic_sync_to_repo.sh ${SOURCE_DB} >> ${LOG_DIR}/db_sync.log 2>&1"
CLEAN_CMD="cd ${REPO_DIR} && ${REPO_DIR}/scripts/birdmic_cleanup_wavs.sh ${BIRDSONGS_DIR} ${CLEAN_DAYS} --delete >> ${LOG_DIR}/wav_cleanup.log 2>&1"

TMP_CRON="$(mktemp)"
crontab -l 2>/dev/null | grep -v "birdmic_sync_to_repo.sh" | grep -v "birdmic_cleanup_wavs.sh" > "${TMP_CRON}" || true
{
  echo ""
  echo "# BirdMic database sync (managed by install_birdmic_cron.sh)"
  echo "${SYNC_SCHEDULE} ${SYNC_CMD}"
  echo "# BirdMic WAV cleanup (managed by install_birdmic_cron.sh)"
  echo "${CLEAN_SCHEDULE} ${CLEAN_CMD}"
} >> "${TMP_CRON}"

crontab "${TMP_CRON}"
rm -f "${TMP_CRON}"

echo "Installed cron jobs:"
echo "  Sync:   ${SYNC_SCHEDULE}"
echo "  Cleanup:${CLEAN_SCHEDULE}"
echo ""
echo "Current crontab:"
crontab -l

