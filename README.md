# MẠCH — Non-Participant Interview Analysis

## Quick Start

### Prerequisites
- Python 3.9+
- Quarto CLI (https://quarto.org/docs/get-started/)
- VS Code + Quarto extension (recommended)

### Render report
```bash
cd mach-nonparticipant-analysis
quarto render report.qmd
```

Output: `_output/report.html` — mở trong browser, share link cho team qua Notion.

### File structure
```
├── _quarto.yml              # Project config
├── report.qmd               # Main report (narrative + code)
├── data/
│   ├── raw/                  # PII data — KHÔNG commit Git
│   └── processed/
│       └── interview_data.py # Structured interview data
├── figures/                  # Charts (auto-generated)
├── _output/                  # Rendered HTML/PDF
└── .gitignore
```

### Workflow cho tour tiếp theo
1. Thu thập interview notes → đưa vào `data/raw/`
2. Structure data → tạo file mới trong `data/processed/`
3. Copy `report.qmd` → sửa narrative + update data source
4. `quarto render` → review → share

### PII Warning
`data/raw/` chứa PII. KHÔNG commit lên Git. KHÔNG share ngoài team.
