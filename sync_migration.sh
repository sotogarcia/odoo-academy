#!/usr/bin/env bash
set -euo pipefail

# Sync selected module directories from 'master' into '18.0' as exact copies.
# Any pre-existing files in 18.0 under those directories will be removed.

TARGET_BRANCH="18.0"
SOURCE_BRANCH="master"
PATHS=(
  "modules/academy_base"
  "modules/academy_facility_management"
  "modules/academy_timesheets"
)

echo "[INFO] Fetching updates…"
git fetch --all --prune

echo "[INFO] Switching to ${TARGET_BRANCH}…"
git switch "${TARGET_BRANCH}"

backup="18.0-pre-sync-$(date +%Y%m%d-%H%M%S)"
echo "[INFO] Creating safety backup branch: ${backup}"
git branch "${backup}"

echo "[INFO] Removing current directories from ${TARGET_BRANCH}…"
git rm -rq --ignore-unmatch "${PATHS[@]}" || true
git clean -fdq -- "${PATHS[@]}" || true

echo "[INFO] Restoring directories from ${SOURCE_BRANCH}…"
git checkout "${SOURCE_BRANCH}" -- "${PATHS[@]}"

echo "[INFO] Staging verification diff:"
git diff --staged || true

echo "[INFO] Committing…"
git commit -m "Sync modules from ${SOURCE_BRANCH}: academy_base, facility_management, timesheets"

echo "[INFO] Pushing to origin/${TARGET_BRANCH}…"
git push origin "${TARGET_BRANCH}"

echo "[DONE] Sync completed successfully."
