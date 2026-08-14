#!/usr/bin/env bash
# Build a portable offline documentation/scripts bundle for air-gapped hosts.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="${1:-$ROOT/dist}"
BUNDLE_NAME="andromeda-offline-bundle-${STAMP}"
STAGE="$OUT_DIR/$BUNDLE_NAME"

mkdir -p "$STAGE"

copy_if_exists() {
  local src="$1"
  local dest="$2"
  if [[ -e "$src" ]]; then
    mkdir -p "$(dirname "$dest")"
    cp -a "$src" "$dest"
  fi
}

echo "Staging offline bundle in $STAGE"

copy_if_exists "$ROOT/README.md" "$STAGE/README.md"
copy_if_exists "$ROOT/LICENSE" "$STAGE/LICENSE"
copy_if_exists "$ROOT/docs" "$STAGE/docs"
copy_if_exists "$ROOT/data" "$STAGE/data"
copy_if_exists "$ROOT/scripts" "$STAGE/scripts"
copy_if_exists "$ROOT/examples" "$STAGE/examples"

cat >"$STAGE/MANIFEST.txt" <<EOF
Andromeda Offline Bundle
created_utc: $STAMP
contents:
  README.md
  LICENSE
  docs/
  data/
  scripts/
  examples/
notes:
  - This bundle includes documentation, catalog data, helper scripts, and example compose files.
  - Container images and model weights are NOT included. Pull them on a networked host first, then transfer separately.
  - Review docs/OFFLINE_FIRST_POLICY.md and docs/SECURITY_CHECKLIST.md before deployment.
EOF

if command -v python3 >/dev/null 2>&1 && [[ -f "$STAGE/scripts/check_catalog.py" ]]; then
  echo "Validating bundled catalog..."
  (cd "$STAGE" && python3 scripts/check_catalog.py)
fi

mkdir -p "$OUT_DIR"
ARCHIVE="$OUT_DIR/${BUNDLE_NAME}.tar.gz"
tar -C "$OUT_DIR" -czf "$ARCHIVE" "$BUNDLE_NAME"

echo "Wrote $ARCHIVE"
echo "Transfer this archive to the offline host, extract it, then follow examples/guardian_stack/README.md"
