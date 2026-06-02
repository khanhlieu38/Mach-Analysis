# AGENTS.md — MẠCH Analysis

Entry point cho Cursor agents. **Đọc theo thứ tự:**

1. **[CONVENTIONS.md](CONVENTIONS.md)** — repo-wide: kiến trúc trang, thứ tự viết, ref_id, freeze Quarto, prose/callout, PII.
2. **[studies/pretour-research-2026/STUDY_RULES.md](studies/pretour-research-2026/STUDY_RULES.md)** — study hiện tại: Rule #1 (compute từ CSV), N=14, schema, taxonomy caveats, terminology, privacy.

**Rule #1 (nhắc nhanh):** Mọi số và quote trong `.qmd` phải compute từ `participants.csv` + `quotes.csv` — không hardcode.

**Hierarchy:** `CONVENTIONS` (repo) → `STUDY_RULES` (study) → prompt (task từng phiên). Không đưa task cụ thể hay trạng thái sprint vào các file rule bền vững.

Study khác: tạo `studies/<study>/STUDY_RULES.md` theo [CONVENTIONS.md](CONVENTIONS.md) mục 7.
