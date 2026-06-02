# MẠCH Analysis

Quarto Website chứa các báo cáo nghiên cứu định tính cho dự án MẠCH — concept tour văn hóa trải nghiệm tại Việt Nam.

## Studies hiện có

- **pretour-research-2026** — 14 phỏng vấn pre-tour, pilot Nam Định 07/2026

## Setup

Prerequisites: Python 3.9+, Quarto CLI, VS Code + Quarto extension.

```bash
quarto preview     # local dev server
quarto render      # build static site → docs/
```

## Writing & Editing

Trước khi viết content, đọc [CONVENTIONS.md](CONVENTIONS.md) (repo-wide) rồi [studies/pretour-research-2026/STUDY_RULES.md](studies/pretour-research-2026/STUDY_RULES.md) (study hiện tại). AI agents: [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md). Cover:

- Document architecture (findings vs audiences) + write order bắt buộc
- Confidence label criteria (Cao / Trung bình / Tín hiệu sớm)
- ref_id format cho audit trail
- CSV scope (what goes in, what doesn't)
- Freeze gotcha workaround khi update CSV
- Prose-forward writing rules + callout discipline

## Structure

```
├── _quarto.yml                      # Website config, navbar
├── index.qmd                        # Landing page
├── shared/
│   ├── styles.css                   # Prose-forward stylesheet
│   └── viz_helpers.py               # Compute helpers + PATTERN_META (markdown tables)
├── studies/
│   └── pretour-research-2026/
│       ├── STUDY_RULES.md           # Sample, schema, taxonomy caveats
│       ├── data/
│       │   ├── participants.csv     # 1 row per participant
│       │   └── quotes.csv           # 1 row per quote/observation
│       ├── overview.qmd
│       ├── methodology.qmd
│       ├── findings.qmd
│       ├── participants.qmd
│       ├── quote-bank.qmd
│       └── audiences/
│           ├── tour-design.qmd
│           ├── content.qmd
│           ├── data.qmd
│           └── finance.qmd
└── docs/                            # Output → GitHub Pages
```

## Thêm study mới

1. Tạo `studies/<segment>-<year>/` theo cùng pattern
2. Thêm `data/participants.csv` + `data/quotes.csv`
3. Copy chapter templates từ `pretour-research-2026/`
4. Cập nhật `_quarto.yml` → thêm navbar menu
5. Cập nhật `index.qmd` → thêm link sang study mới

## Import pattern cho chapters dùng Python

```python
import sys
from pathlib import Path

def _find_root(start):
    for p in [start] + list(start.parents):
        if (p / "_quarto.yml").exists():
            return p
    return start

_root = _find_root(Path.cwd())
sys.path.insert(0, str(_root / "shared"))

from viz_helpers import load_study_data, pattern_occurrence, patterns_summary_table

participants_df, quotes_df = load_study_data(_root / "studies" / "pretour-research-2026")
```

## PII Warning

`studies/*/data/raw/` chứa PII. KHÔNG commit lên Git. KHÔNG share ngoài team.
