# MẠCH Analysis

Quarto website chứa các báo cáo nghiên cứu định tính cho dự án MẠCH, một concept tour văn hóa trải nghiệm tại Việt Nam. `README.md` là nguồn hướng dẫn đầy đủ duy nhất cho setup, cấu trúc, dữ liệu, privacy, render/deploy, writing conventions, và workflow cho AI agents.

## Current Study

**`pretour-research-2026`** là single-page consumer research report cho pilot Nam Định 07/2026.

- Report public source: `studies/pretour-research-2026/index.qmd`
- Study-specific rules: `studies/pretour-research-2026/STUDY_RULES.md`
- Output directory: `docs/`
- Sample: `participants.csv` computes to N=15
- Full compiled record: `records.csv` has 143 quote/record entries
- Curated evidence bank: `quotes.csv` supports report claims and pattern occurrence

## Folder Structure

```text
├── _quarto.yml
├── README.md
├── index.qmd
├── deploy.ps1
├── deploy.sh
├── shared/
│   ├── styles.css
│   └── viz_helpers.py
├── studies/
│   └── pretour-research-2026/
│       ├── index.qmd
│       ├── STUDY_RULES.md
│       ├── data/
│       │   ├── participants.csv
│       │   ├── records.csv
│       │   ├── quotes.csv
│       │   └── raw/
│       └── _archive/
│           └── multipage-v1/
└── docs/
```

`_archive/` folders are historical source only and should not be rendered as public pages.

## Setup And Render

Prerequisites:

- Python 3.9+
- Quarto CLI
- VS Code or Cursor with Quarto support
- Node/npm only if deploying with StatiCrypt

Install the pinned project dependencies:

```bash
python -m pip install -r requirements.txt
npm ci
```

Local preview and render:

```bash
quarto preview
quarto render
```

The site renders to `docs/`. Current `_quarto.yml` intentionally renders only the root landing page and the final single-page study report.

## Data Model

`participants.csv` is the anonymized sample source. One row equals one participant using a stable P-code such as `P01`. Age is stored only as a broad band, occupations are generalized, and `note` is provenance-only. Detailed profiles belong in ignored `data/raw/` storage.

`records.csv` is the full compiled participant record table. For `pretour-research-2026`, it is extracted from `data/raw/MACH_participant_record_compiled.pdf` and contains 143 entries. It preserves the full reviewable quote/record layer, with `source_status` marking quotes as `participant quote, edited for clarity`.

`quotes.csv` is a curated evidence bank for report claims. It is not the full record table. It contains coded quotes/observations used for pattern occurrence, evidence tables, and selected report support.

`data/raw/` contains private source material and may contain PII. Do not render raw files, link raw files from public pages, or copy real names into public `.qmd`, `docs/`, or committed analysis tables.

## Rule #1: Compute From Data

All computable numbers, counts, denominators, quote counts, pattern occurrence, and selected quote/evidence tables in `.qmd` must be computed from CSVs and helpers, not hardcoded in prose.

Use or extend `shared/viz_helpers.py` for reusable computation. If a number cannot be computed from committed structured data, either add the source data first or label the claim as qualitative with a confidence caveat.

Common import pattern:

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

from viz_helpers import load_study_data, load_records_data

study_dir = _root / "studies" / "pretour-research-2026"
participants_df, quotes_df = load_study_data(study_dir)
records_df = load_records_data(study_dir)
```

## Privacy And PII

- Use P-codes in reports and committed structured analysis files.
- Do not expose names, phone numbers, Zalo, email, company-identifying details, consent forms, raw transcripts, audio, photos, or crosswalk files in rendered output.
- `studies/*/data/raw/` is private source material. Treat it as non-rendered and internal-only.
- Crosswalks from P-code to real name belong only in private raw storage.
- Do not commit exact ages/birth years, employer or organization names, detailed family profiles, or combined quasi-identifiers. Generalize them before they enter structured committed data.
- If output is ever shared outside MẠCH, anonymize again and check consent/legal requirements first.
- If a quote comes from polished compiled notes and has not been checked against audio/transcript, label it as `participant quote, edited for clarity` or avoid presenting it as verbatim.

## Confidence Labels

Use confidence labels consistently in findings and evidence tables:

| Label | Criteria |
|---|---|
| **Cao** | At least 5 independent sources in the sample, with no direct contradiction; strong enough for pilot decisions. |
| **Trung bình** | Clear signal but not saturated, or meaningful disagreement requiring another cohort/pilot validation. |
| **Tín hiệu sớm** | 1-2 sources; worth tracking, not enough for a firm conclusion. |
| **Hypothesis** | Inferred from related patterns or absent segment; requires direct testing. |

CSV values use `cao`, `trung_binh`, `som`, and `hypothesis`. Pattern-level confidence for the current study is maintained in `shared/viz_helpers.py` and refined in `STUDY_RULES.md`.

## ref_id Audit Trail

Every curated evidence row in `quotes.csv` must have a non-empty `ref_id`.

Format:

```text
<SOURCE_TYPE>_<PARTICIPANT_ID>_<YEAR>Q<QUARTER>_<POSITION>
```

Examples:

- `T_P01_2026Q2_p12` means transcript text for P01, page 12.
- `A_P05_2026Q2_t0830` means audio timestamp 08:30 for P05.
- `F_P15_2026Q2_r140` means field/compiled record evidence for P15, record 140.

Use stable IDs when creating or updating quotes. Do not retrofit audit trails later.

## Writing Style

The report is prose-forward. Write for business and research decisions, not dashboards.

Do:

- Use short narrative bridges between sections.
- Use markdown tables for compact comparisons.
- Keep quotes as standalone blockquotes when writing prose manually.
- Attribute quotes with P-codes only.
- Use confidence labels near claims.
- Keep callouts rare and purposeful.

Do not:

- Stack many quote cards or grids.
- Put KPI-style big numbers at the top for small qualitative samples.
- Bold every key phrase.
- Claim representativeness.
- Invent findings not supported by CSVs, records, archived analysis, or raw source material.

Preferred manual quote format:

```markdown
> "Quote text."
>
> — **P05**, participant quote, edited for clarity
```

## Quarto Freeze / Cache Warning

Quarto `freeze: auto` can cache execution output based on `.qmd` changes, not data changes. If you update CSVs or helpers, force a fresh render.

Preferred validation render:

```bash
quarto render
```

If your installed Quarto supports it:

```bash
quarto render --no-freeze
```

If outputs look stale, clear `_freeze/` and render again:

```bash
rm -rf _freeze/
quarto render
```

On Windows PowerShell:

```powershell
Remove-Item -Recurse -Force _freeze/
quarto render
```

## Deploy

Deploy scripts render into a staging directory, validate raw output, encrypt every HTML file in place with the pinned local StatiCrypt, validate the encrypted tree, then replace and publish `docs/`. A failed render or encryption leaves the previous `docs/` intact.

Set the password outside the repo. Do not commit passwords.

Windows PowerShell:

```powershell
$env:MACH_PASSWORD = "your-password-here"
.\deploy.ps1
```

Git Bash / macOS:

```bash
export MACH_PASSWORD="your-password-here"
bash deploy.sh
```

Build and validate encrypted `docs/` without committing or pushing:

```powershell
.\deploy.ps1 -BuildOnly
```

```bash
bash deploy.sh --build-only
```

If `MACH_PASSWORD` is not set, the scripts prompt for it. The scripts use `staticrypt` with remember duration and custom Vietnamese prompt text.

Security notes:

- Do not share the password by email.
- Do not store passwords in repo files.
- `.staticrypt.json` contains encryption salt, not the password; it may be committed if present.
- Changing the password requires rerunning deploy so HTML is re-encrypted.

Local encrypted-output check:

```powershell
Start-Process docs\index.html
```

```bash
open docs/index.html
```

You should see the password prompt before accessing the report.

## Validation Checklist

Before commit or deploy:

1. Run the structured data/privacy/interaction checks:

   ```bash
   python scripts/validate_repo.py
   ```

2. Confirm no private audit term appears in committed source or rendered output. Keep the term list under ignored `data/raw/`, never in Git.

3. Confirm retired standalone docs are not referenced in active files and obsolete sample-size wording is gone.

4. Confirm source counts and tracker reconciliation via `scripts/validate_repo.py`.

5. Render and require a warning-free build:

   ```bash
   quarto render
   ```

6. Run `python scripts/test_deploy_layout.py` to confirm duplicate HTML basenames remain encrypted at their original paths.

7. If deploying, run the appropriate deploy script and verify both encrypted HTML paths plus the StatiCrypt password prompt.

## AI Agent Workflow

AI agents must read this `README.md` first, then the target study's `STUDY_RULES.md`.

Workflow:

1. Inspect relevant source files before editing.
2. Keep report structure stable unless explicitly asked to restructure.
3. Do not modify raw data or report data unless the task is data reconciliation.
4. Do not expose PII.
5. Use `shared/viz_helpers.py` for reusable computation.
6. Keep all counts and evidence computed from CSVs/helpers.
7. Run targeted searches and `quarto render` after substantive changes.
8. Report unresolved data gaps instead of making numbers look right.

Study-specific rules override this README when they are more specific. The user prompt overrides both for the current task unless it would violate privacy, data integrity, or build safety.

## Add A New Study

1. Create `studies/<study-name>/`.
2. Add `STUDY_RULES.md` with sample, schema, taxonomy, terminology, privacy caveats, and confidence rules.
3. Add `data/participants.csv`.
4. Add `data/records.csv` if there is a compiled full record table.
5. Add `data/quotes.csv` for curated evidence used by the report.
6. Keep raw source material in `data/raw/` and make sure it is not rendered.
7. Create `index.qmd` as the public single-page report.
8. Use `shared/viz_helpers.py` or add generic helpers there.
9. Update `_quarto.yml` render/navbar only for pages that should be public.
10. Update root `index.qmd` with a link to the new study.
