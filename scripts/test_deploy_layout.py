#!/usr/bin/env python3
"""Regression test: duplicate HTML basenames must remain encrypted in place."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from validate_site import validate_encrypted, validate_layout


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    npx = "npx.cmd" if os.name == "nt" else "npx"
    with tempfile.TemporaryDirectory(prefix=".mach-staticrypt-", dir=ROOT) as temp_dir:
        site = Path(temp_dir) / "site"
        paths = [site / "index.html", site / "nested" / "index.html"]
        for index, path in enumerate(paths, start=1):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f'<!doctype html><html><body><main id="quarto-document-content">fixture {index}</main></body></html>',
                encoding="utf-8",
            )
        for path in paths:
            subprocess.run(
                [
                    npx, "--no-install", "staticrypt", str(path),
                    "--directory", str(path.parent),
                    "--password", "qa-dummy-password",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        errors = validate_layout(site, require_site_layout=False)
        errors.extend(validate_encrypted(site))
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        if {path.relative_to(site) for path in site.rglob("*.html")} != {
            Path("index.html"), Path("nested/index.html")
        }:
            print("ERROR: duplicate HTML basenames were flattened")
            return 1
    print("OK: duplicate HTML basenames remain encrypted at their original paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
