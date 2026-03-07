#!/usr/bin/env bash
set -euo pipefail

# Clean up old BirdNET-Pi WAV files to prevent SD card exhaustion.
#
# Default behavior is DRY RUN (prints files, does not delete).
#
# Usage:
#   scripts/birdmic_cleanup_wavs.sh [BIRDSONGS_DIR] [DAYS_OLD]
#
# Examples:
#   scripts/birdmic_cleanup_wavs.sh
#   scripts/birdmic_cleanup_wavs.sh /home/birdnet/BirdNET-Pi/BirdSongs 14
#   scripts/birdmic_cleanup_wavs.sh /home/birdnet/BirdNET-Pi/BirdSongs 14 --delete
#
# Flags:
#   --delete    Actually delete matching files.

BIRDSONGS_DIR="${1:-/home/birdnet/BirdNET-Pi/BirdSongs}"
DAYS_OLD="${2:-14}"
DO_DELETE="false"

if [[ "${*: -1}" == "--delete" ]]; then
  DO_DELETE="true"
fi

if [[ ! -d "${BIRDSONGS_DIR}" ]]; then
  echo "ERROR: BirdSongs directory not found: ${BIRDSONGS_DIR}"
  exit 1
fi

if ! [[ "${DAYS_OLD}" =~ ^[0-9]+$ ]]; then
  echo "ERROR: DAYS_OLD must be an integer."
  exit 1
fi

echo "BirdSongs dir: ${BIRDSONGS_DIR}"
echo "Matching WAV files older than ${DAYS_OLD} day(s)"
echo "Mode: $([[ "${DO_DELETE}" == "true" ]] && echo "DELETE" || echo "DRY RUN")"

MATCH_COUNT="$(find "${BIRDSONGS_DIR}" -type f -name "*.wav" -mtime +"${DAYS_OLD}" | wc -l)"
echo "Matches: ${MATCH_COUNT}"

if [[ "${MATCH_COUNT}" == "0" ]]; then
  echo "No files to process."
  exit 0
fi

if [[ "${DO_DELETE}" == "true" ]]; then
  find "${BIRDSONGS_DIR}" -type f -name "*.wav" -mtime +"${DAYS_OLD}" -print -delete
  echo "Deleted ${MATCH_COUNT} file(s)."
else
  find "${BIRDSONGS_DIR}" -type f -name "*.wav" -mtime +"${DAYS_OLD}" -print
  echo "Dry run complete. Re-run with --delete to remove files."
fi

