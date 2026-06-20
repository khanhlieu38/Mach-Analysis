#!/usr/bin/env python3
"""Inject a self-reporting click/keyboard smoke test into rendered report HTML."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SCRIPT = r"""
<script>
window.addEventListener('DOMContentLoaded', function () {
  window.setTimeout(function () {
    var slide = document.querySelector('#visual-p1');
    var controls = slide ? slide.querySelectorAll('[data-b-pids],[data-b-qids]') : [];
    var panel = slide ? slide.querySelector('.deck-b-quote-panel') : null;
    var results = {slide: !!slide, controls: controls.length, panel: !!panel};
    if (controls.length && panel) {
      controls[0].click();
      results.clickOpened = !panel.hidden && controls[0].classList.contains('b-active');
      document.body.click();
      controls[0].dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
      results.keyboardOpened = !panel.hidden && controls[0].getAttribute('aria-expanded') === 'true';
      results.visibleQuotes = panel.querySelectorAll('.bqp-quote:not(.bqp-hidden)').length;
    }
    results.pass = !!(
      results.slide && results.controls > 0 && results.panel && results.clickOpened &&
      results.keyboardOpened && results.visibleQuotes > 0
    );
    document.body.innerHTML = '<pre id="browser-smoke-result">' + JSON.stringify(results) + '</pre>';
    document.title = results.pass ? 'BROWSER_SMOKE_PASS' : 'BROWSER_SMOKE_FAIL';
  }, 0);
});
</script>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--section")
    args = parser.parse_args()
    html = args.input.read_text(encoding="utf-8")
    if args.section:
        head_match = re.search(r"<head[^>]*>(.*)</head>", html, flags=re.DOTALL | re.IGNORECASE)
        section_match = re.search(
            rf'<section\s+id="{re.escape(args.section)}"[^>]*>.*?</section>',
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if head_match is None or section_match is None:
            raise SystemExit(f"rendered HTML is missing section #{args.section}")
        base_uri = args.input.resolve().parent.as_uri() + "/"
        fixture = (
            '<!doctype html><html><head><base href="'
            + base_uri
            + '">'
            + head_match.group(1)
            + "</head><body>"
            + section_match.group(0)
            + "</body></html>"
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(fixture, encoding="utf-8")
        print(f"visual section fixture created: {args.output}")
        return 0
    body_match = re.search(r"<body[^>]*>(.*)</body>", html, flags=re.DOTALL | re.IGNORECASE)
    if body_match is None:
        raise SystemExit("rendered HTML has no closing body tag")
    fixture = (
        '<!doctype html><html><head><meta charset="utf-8"><title>browser smoke</title></head><body>'
        + body_match.group(1)
        + SCRIPT
        + "</body></html>"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(fixture, encoding="utf-8")
    print(f"browser smoke fixture created: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
