#!/usr/bin/env bash
# Build a portable offline documentation/scripts bundle for air-gapped hosts.
set -euo pipefail
shopt -s nullglob globstar

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="${1:-$ROOT/dist}"
BUNDLE_NAME="andromeda-offline-bundle-${STAMP}"
STAGE="$OUT_DIR/$BUNDLE_NAME"

mkdir -p "$OUT_DIR"
if [[ -e "$STAGE" ]]; then
  echo "Refusing to reuse existing stage directory: $STAGE" >&2
  exit 1
fi
mkdir -p "$STAGE"

# Fail closed: package only reviewed source/documentation types. Never copy the
# whole gateway working tree, where ignored secrets and runtime state may live.
SOURCES=(
  "$ROOT/README.md"
  "$ROOT/LICENSE"
  "$ROOT/docs/"*.md
  "$ROOT/data/"*.json
  "$ROOT/scripts/"*.py
  "$ROOT/scripts/"*.sh
  "$ROOT/examples/"**/*.md
  "$ROOT/examples/"**/*.yml
  "$ROOT/examples/"**/*.yaml
  "$ROOT/examples/"**/Caddyfile
  "$ROOT/gateway/README.md"
  "$ROOT/gateway/config.example.yaml"
  "$ROOT/gateway/pytest.ini"
  "$ROOT/gateway/requirements.txt"
  "$ROOT/gateway/requirements-dev.txt"
  "$ROOT/gateway/andromeda_gateway/"**/*.py
  "$ROOT/gateway/tests/"**/*.py
)

echo "Staging offline bundle in $STAGE"
for src in "${SOURCES[@]}"; do
  [[ -f "$src" ]] || continue
  rel="${src#"$ROOT"/}"
  dest="$STAGE/$rel"
  mkdir -p "$(dirname "$dest")"
  cp -p "$src" "$dest"
done

forbidden_entry="$(
  find "$STAGE" -type f \( \
    -name '.env' -o -name '.env.*' -o -name 'config.yaml' -o \
    -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' -o \
    -name '*.pem' -o -name '*.key' \
  \) -print -quit
)"
if [[ -n "$forbidden_entry" ]]; then
  echo "Refusing to package sensitive or runtime file: $forbidden_entry" >&2
  exit 1
fi

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
  gateway/
notes:
  - Source files are copied from a strict allowlist; local config, secrets, databases, caches, and virtualenvs are excluded.
  - Container images and model weights are NOT included. Pull them on a networked host first, then transfer separately.
  - Review docs/OFFLINE_FIRST_POLICY.md and docs/SECURITY_CHECKLIST.md before deployment.
EOF

if command -v python3 >/dev/null 2>&1 && [[ -f "$STAGE/scripts/check_catalog.py" ]]; then
  echo "Validating bundled catalog..."
  (cd "$STAGE" && python3 scripts/check_catalog.py)
fi

ARCHIVE="$OUT_DIR/${BUNDLE_NAME}.tar.gz"
tar -C "$OUT_DIR" -czf "$ARCHIVE" "$BUNDLE_NAME"
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "$ARCHIVE" >"$ARCHIVE.sha256"
else
  shasum -a 256 "$ARCHIVE" >"$ARCHIVE.sha256"
fi

echo "Wrote $ARCHIVE"
echo "Wrote $ARCHIVE.sha256"
echo "Transfer both files to the offline host, verify the checksum, then extract the archive."
