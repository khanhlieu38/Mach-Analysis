#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

STAGING="$ROOT/.deploy-staging"
BACKUP="$ROOT/.deploy-backup"
DOCS="$ROOT/docs"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BUILD_ONLY=0

if [ "${1:-}" = "--build-only" ]; then
  BUILD_ONLY=1
  shift
fi
if [ "$#" -ne 0 ]; then
  echo "Usage: $0 [--build-only]" >&2
  exit 2
fi

safe_remove() {
  case "$1" in
    "$STAGING"|"$BACKUP")
      [ ! -e "$1" ] || rm -rf -- "$1"
      ;;
    *)
      echo "Refusing to remove unexpected directory: $1" >&2
      exit 1
      ;;
  esac
}

for command in quarto npx "$PYTHON_BIN"; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "Missing required command: $command" >&2
    exit 1
  }
done
if [ "$BUILD_ONLY" -eq 0 ]; then
  command -v git >/dev/null 2>&1 || {
    echo "Missing required command: git" >&2
    exit 1
  }
fi

if [ -z "${MACH_PASSWORD:-}" ]; then
  read -rsp "Nhập mật khẩu MẠCH: " MACH_PASSWORD
  echo
fi
if [ -z "${MACH_PASSWORD:-}" ]; then
  echo "Lỗi: password không được để trống." >&2
  exit 1
fi

safe_remove "$STAGING"
safe_remove "$BACKUP"

cleanup() {
  safe_remove "$STAGING"
  if [ -d "$BACKUP" ] && [ ! -d "$DOCS" ]; then
    mv "$BACKUP" "$DOCS"
  fi
}
trap cleanup EXIT

echo "→ Rendering Quarto site into staging..."
quarto render --output-dir .deploy-staging
rm -f -- "$STAGING/search.json"

"$PYTHON_BIN" scripts/validate_site.py raw "$STAGING" --require-site-layout

expected_paths="$(find "$STAGING" -type f -name '*.html' -print | sed "s#^$STAGING/##" | sort)"
if [ -z "$expected_paths" ]; then
  echo "Lỗi: không tìm thấy HTML files trong staging." >&2
  exit 1
fi

echo "→ Encrypting HTML files in place..."
while IFS= read -r file; do
  npx --no-install staticrypt "$file" \
    --directory "$(dirname "$file")" \
    --password "$MACH_PASSWORD" \
    --remember 7 \
    --template-title "MẠCH — Báo cáo Nghiên cứu" \
    --template-instructions "Nhập mật khẩu để truy cập" \
    --template-button "Truy cập"
done < <(find "$STAGING" -type f -name '*.html' -print)

actual_paths="$(find "$STAGING" -type f -name '*.html' -print | sed "s#^$STAGING/##" | sort)"
if [ "$expected_paths" != "$actual_paths" ]; then
  echo "Encrypted HTML paths do not match raw staging paths." >&2
  exit 1
fi

"$PYTHON_BIN" scripts/validate_site.py encrypted "$STAGING" --require-site-layout

had_docs=0
if [ -d "$DOCS" ]; then
  mv "$DOCS" "$BACKUP"
  had_docs=1
fi
if ! mv "$STAGING" "$DOCS"; then
  if [ "$had_docs" -eq 1 ] && [ -d "$BACKUP" ]; then
    mv "$BACKUP" "$DOCS"
  fi
  exit 1
fi
safe_remove "$BACKUP"

if [ "$BUILD_ONLY" -eq 1 ]; then
  echo "✓ Encrypted docs/ built and validated; Git was not changed."
  exit 0
fi

echo "→ Publishing encrypted docs/..."
git add docs/
if git diff --cached --quiet -- docs/; then
  echo "No encrypted output changes; skipping commit and push."
  exit 0
fi

git commit -m "Deploy: update encrypted site $(date +'%Y-%m-%d %H:%M')"
git push

echo "✓ Done. Site live tại https://khanhlieu38.github.io/Mach-Analysis/"
