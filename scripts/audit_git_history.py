#!/usr/bin/env python3
"""Fail when private audit terms remain in any blob reachable from local refs."""

from __future__ import annotations

import argparse
import io
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TERMS = (
    ROOT
    / "studies"
    / "pretour-research-2026"
    / "data"
    / "raw"
    / "privacy_audit_terms.txt"
)


def run_git(*args: str, input_text: str | None = None) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        input=input_text,
    ).stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--terms", type=Path, default=DEFAULT_TERMS)
    args = parser.parse_args()

    term_file = args.terms.resolve()
    if not term_file.is_file():
        raise SystemExit(f"private audit term file not found: {term_file}")
    terms = [
        line.strip().casefold()
        for line in term_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not terms:
        raise SystemExit("private audit term list is empty")

    object_paths: dict[str, set[str]] = defaultdict(set)
    for line in run_git("rev-list", "--objects", "--all").splitlines():
        oid, _, path = line.partition(" ")
        if path:
            object_paths[oid].add(path)
        else:
            object_paths.setdefault(oid, set())

    object_ids = list(object_paths)
    check_input = "".join(f"{oid}\n" for oid in object_ids)
    checks = run_git(
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        input_text=check_input,
    ).splitlines()
    blobs = []
    for line in checks:
        oid, object_type, size = line.split()
        if object_type == "blob" and int(size) <= 5_000_000:
            blobs.append(oid)

    process = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=ROOT,
        input="".join(f"{oid}\n" for oid in blobs).encode("ascii"),
        capture_output=True,
        check=True,
    )
    output = io.BytesIO(process.stdout)

    findings: list[tuple[int, list[str]]] = []
    for expected_oid in blobs:
        header = output.readline().decode("ascii").strip()
        oid, object_type, size_text = header.split()
        if oid != expected_oid or object_type != "blob":
            raise RuntimeError(f"unexpected git cat-file header: {header}")
        content = output.read(int(size_text))
        output.read(1)
        text = content.decode("utf-8", errors="ignore").casefold()
        for index, term in enumerate(terms, start=1):
            if term in text:
                paths = sorted(object_paths.get(oid) or {f"blob:{oid}"})
                findings.append((index, paths))
    if findings:
        for index, paths in findings:
            print(f"ERROR: sensitive term #{index} remains in: {', '.join(paths)}")
        return 1
    print(f"OK: {len(blobs)} reachable Git blobs contain none of {len(terms)} private terms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
