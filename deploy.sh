#!/usr/bin/env bash
set -e

# ── 1. Password ───────────────────────────────────────────────────
if [ -z "$MACH_PASSWORD" ]; then
  read -rsp "Nhập mật khẩu MẠCH: " MACH_PASSWORD
  echo
fi

if [ -z "$MACH_PASSWORD" ]; then
  echo "Lỗi: password không được để trống."
  exit 1
fi

# ── 2. Render ─────────────────────────────────────────────────────
echo "→ Rendering Quarto site..."
quarto render

if [ -f docs/search.json ]; then
  rm docs/search.json
  echo "→ Removed raw Quarto search index."
fi

# ── 3. Encrypt ────────────────────────────────────────────────────
echo "→ Encrypting docs/ with StatiCrypt..."

mapfile -d '' HTML_FILES < <(find docs -name "*.html" -print0)

if [ ${#HTML_FILES[@]} -eq 0 ]; then
  echo "Lỗi: không tìm thấy HTML files trong docs/"
  exit 1
fi

staticrypt "${HTML_FILES[@]}" \
  --directory docs \
  --password "$MACH_PASSWORD" \
  --remember 7 \
  --template-title "MẠCH — Báo cáo Nghiên cứu" \
  --template-instructions "Nhập mật khẩu để truy cập" \
  --template-button "Truy cập"

# ── 4. Push ───────────────────────────────────────────────────────
echo "→ Pushing to GitHub Pages..."
git add docs/
git commit -m "Deploy: update encrypted site $(date +'%Y-%m-%d %H:%M')"
git push

echo "✓ Done. Site live tại https://khanhlieu38.github.io/Mach-Analysis/"
