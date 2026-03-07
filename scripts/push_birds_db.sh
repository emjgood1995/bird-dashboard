#!/usr/bin/env bash
set -euo pipefail

# Copy a source SQLite database into birds_lfs.db, then commit+push if changed.
#
# Usage:
#   scripts/push_birds_db.sh /absolute/path/to/source.db
#
# Optional env vars:
#   REPO_DIR      (default: current working directory)
#   TARGET_FILE   (default: birds_lfs.db)
#   REMOTE_NAME   (default: origin)
#   BRANCH_NAME   (default: main)

SOURCE_DB="${1:-}"
REPO_DIR="${REPO_DIR:-$(pwd)}"
TARGET_FILE="${TARGET_FILE:-birds_lfs.db}"
REMOTE_NAME="${REMOTE_NAME:-origin}"
BRANCH_NAME="${BRANCH_NAME:-main}"

if [[ -z "${SOURCE_DB}" ]]; then
  echo "ERROR: missing source db path."
  echo "Usage: $0 /absolute/path/to/source.db"
  exit 1
fi

if [[ ! -f "${SOURCE_DB}" ]]; then
  echo "ERROR: source db not found: ${SOURCE_DB}"
  exit 1
fi

if [[ ! -d "${REPO_DIR}/.git" ]]; then
  echo "ERROR: REPO_DIR is not a git repository: ${REPO_DIR}"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is not installed."
  exit 1
fi

if ! git -C "${REPO_DIR}" lfs version >/dev/null 2>&1; then
  echo "ERROR: git-lfs is not available."
  exit 1
fi

LOCK_DIR="${REPO_DIR}/.push_birds_db.lock"
if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
  echo "Another sync appears to be running. Exiting."
  exit 0
fi
trap 'rmdir "${LOCK_DIR}" >/dev/null 2>&1 || true' EXIT

push_pending_commits() {
  local ahead_count
  ahead_count="$(git -C "${REPO_DIR}" rev-list --count "${REMOTE_NAME}/${BRANCH_NAME}..${BRANCH_NAME}" 2>/dev/null || echo 0)"
  if [[ "${ahead_count}" -gt 0 ]]; then
    echo "Local branch is ahead by ${ahead_count} commit(s). Pushing pending commits."
    # Explicit LFS upload avoids reliance on possibly non-executable git hooks.
    git -C "${REPO_DIR}" lfs push "${REMOTE_NAME}" "${BRANCH_NAME}"
    git -C "${REPO_DIR}" push "${REMOTE_NAME}" "${BRANCH_NAME}"
  fi
}

# Ensure we are up to date before touching the working copy.
git -C "${REPO_DIR}" fetch "${REMOTE_NAME}" "${BRANCH_NAME}"
git -C "${REPO_DIR}" pull --ff-only "${REMOTE_NAME}" "${BRANCH_NAME}"

TARGET_PATH="${REPO_DIR}/${TARGET_FILE}"
TMP_PATH="${TARGET_PATH}.tmp"

# Copy atomically via temp file.
cp "${SOURCE_DB}" "${TMP_PATH}"

if [[ -f "${TARGET_PATH}" ]] && cmp -s "${TMP_PATH}" "${TARGET_PATH}"; then
  rm -f "${TMP_PATH}"
  # Source equals working copy. Still stage in case TARGET_FILE is pending relative to HEAD.
  git -C "${REPO_DIR}" add "${TARGET_FILE}"
  if git -C "${REPO_DIR}" diff --cached --quiet; then
    push_pending_commits
    echo "No database changes detected. Nothing to commit."
    exit 0
  fi
else
  mv -f "${TMP_PATH}" "${TARGET_PATH}"
  git -C "${REPO_DIR}" add "${TARGET_FILE}"
fi

if git -C "${REPO_DIR}" diff --cached --quiet; then
  echo "No staged changes after update. Nothing to commit."
  exit 0
fi

STAMP="$(date -u +"%Y-%m-%d %H:%M:%S UTC")"
git -C "${REPO_DIR}" commit -m "Automated DB update: ${STAMP}"
# Explicit LFS upload avoids reliance on possibly non-executable git hooks.
git -C "${REPO_DIR}" lfs push "${REMOTE_NAME}" "${BRANCH_NAME}"
git -C "${REPO_DIR}" push "${REMOTE_NAME}" "${BRANCH_NAME}"

echo "Database sync committed and pushed successfully."
