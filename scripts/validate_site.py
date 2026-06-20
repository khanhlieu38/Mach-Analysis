#!/usr/bin/env python3
"""Validate raw Quarto output or StatiCrypt-encrypted site output."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


FORBIDDEN_SUFFIXES = {".csv", ".qmd", ".ipynb", ".pdf"}
REQUIRED_SITE_HTML = {
    Path("index.html"),
    Path("studies/pretour-research-2026/index.html"),
}


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        for key in ("href", "src"):
            value = values.get(key)
            if value:
                self.links.append(value)


def html_paths(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in root.rglob("*.html")}


def validate_layout(root: Path, require_site_layout: bool) -> list[str]:
    errors: list[str] = []
    paths = html_paths(root)
    if not paths:
        errors.append("no HTML files found")
    if require_site_layout:
        missing = REQUIRED_SITE_HTML - paths
        if missing:
            errors.append(f"missing required HTML paths: {sorted(map(str, missing))}")
    if (root / "search.json").exists():
        errors.append("search.json must not be published")
    forbidden = [
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    if forbidden:
        errors.append(f"forbidden published files: {sorted(map(str, forbidden))}")
    return errors


def validate_raw(root: Path) -> list[str]:
    errors: list[str] = []
    for html_path in root.rglob("*.html"):
        parser = LinkCollector()
        parser.feed(html_path.read_text(encoding="utf-8"))
        for raw_link in parser.links:
            if raw_link.startswith(("data:", "mailto:", "tel:", "javascript:")):
                continue
            parsed = urlparse(raw_link)
            if parsed.scheme in {"http", "https"}:
                continue
            if parsed.scheme:
                continue
            if not parsed.path and parsed.fragment:
                if unquote(parsed.fragment) not in parser.ids:
                    errors.append(
                        f"{html_path.relative_to(root)}: missing anchor #{parsed.fragment}"
                    )
                continue
            target = (html_path.parent / unquote(parsed.path)).resolve()
            if not target.exists():
                errors.append(
                    f"{html_path.relative_to(root)}: missing local asset {parsed.path}"
                )
    return errors


def validate_encrypted(root: Path) -> list[str]:
    errors: list[str] = []
    plaintext_markers = (
        'id="quarto-document-content"',
        'class="deck-slide',
        "data-b-pids=",
    )
    for html_path in root.rglob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        lowered = text.lower()
        if "staticrypt" not in lowered:
            errors.append(f"{html_path.relative_to(root)}: missing StatiCrypt marker")
        for marker in plaintext_markers:
            if marker in text:
                errors.append(
                    f"{html_path.relative_to(root)}: plaintext marker remains: {marker}"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("raw", "encrypted"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--require-site-layout", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"site directory not found: {root}")

    errors = validate_layout(root, args.require_site_layout)
    errors.extend(validate_raw(root) if args.mode == "raw" else validate_encrypted(root))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {args.mode} site validated ({len(html_paths(root))} HTML files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
