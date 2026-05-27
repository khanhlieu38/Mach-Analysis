# MẠCH Analysis — Conventions

Tài liệu này là **contract** giữa người viết content (analyst), stylesheet, và repo structure. Đọc trước khi fill content vào bất kỳ chapter nào.

---

## 1. Document architecture — write order quan trọng

Repo có 2 lớp pages, vai trò khác nhau:

**Lớp analytical (one source of truth):**
- `studies/<study>/findings.qmd` — phân tích đầy đủ, 3 patterns + signals
- `studies/<study>/participants.qmd` — 12 deep dives
- `studies/<study>/methodology.qmd` — phương pháp, limitations

**Lớp audience (filtered views, extract từ analytical):**
- `studies/<study>/audiences/tour-design.qmd` — cho Tour Design Team
- `studies/<study>/audiences/content.qmd` — cho Content & Media Team
- `studies/<study>/audiences/data.qmd` — cho Data Team
- `studies/<study>/audiences/finance.qmd` — cho Finance Team

**Quan trọng:** Audiences KHÔNG phải duplicate analysis. Là cùng findings, được filter + synthesize cho từng decision-maker. Đây là Product Thinking applied to docs.

**Write order bắt buộc:**

1. Fill data (CSVs) — `participants.csv` + `quotes.csv`
2. Write `findings.qmd` (one source of truth)
3. Write `participants.qmd` (12 deep dives)
4. Write `methodology.qmd`
5. Write `audiences/*.qmd` — extract relevant findings, KHÔNG re-analyze

Viết audiences trước findings = inconsistency, rework, mâu thuẫn nội dung.

---

## 2. Confidence labels — methodological key

Mọi pattern/finding trong `findings.qmd` phải gắn confidence label. Field `confidence_level` trong `quotes.csv` dùng cùng convention.

| Label | Criteria | Ví dụ |
|:--|:--|:--|
| **Cao** | ≥8/12 participants + thematic saturation đạt | Tour Design issue |
| **Trung bình** | 4-7/12, pattern rõ nhưng chưa fully saturated | Identity Mismatch |
| **Tín hiệu sớm** | ≤3/12, đáng flag nhưng cần research thêm | Phụ nữ tâm linh (2/12) |

Render label inline trong prose (vd: *"Pattern này xuất hiện ở 10/12 participants — confidence Cao."*) hoặc dạng callout small. Không để mọi finding trông equal weight.

Đây là tư duy **"Limitations chuyên nghiệp, không xin lỗi"** — confidence label không phải caveat, là honest signal về độ tin cậy.

---

## 3. ref_id format — audit trail

Mỗi row trong `quotes.csv` PHẢI có `ref_id` non-empty.

**Format:** `<SOURCE_TYPE>_<PARTICIPANT_ID>_<YEAR>Q<QUARTER>_<POSITION>`

- **SOURCE_TYPE:** `T` (transcript text), `F` (field notes), `G` (focus group), `A` (audio timestamp)
- **PARTICIPANT_ID:** matches `pid` trong `participants.csv` (P01-P12)
- **YEAR + QUARTER:** khi phỏng vấn (vd `2026Q2`)
- **POSITION:** page number nếu text (`p12`), timestamp nếu audio (`t0245` = 02:45)

**Ví dụ:**
- `T_P01_2026Q2_p12` — transcript của P01, Q2/2026, page 12
- `A_P05_2026Q2_t0830` — audio của P05, timestamp 08:30
- `F_P09_2026Q3_p3` — field notes của P09, Q3/2026, page 3

**Tại sao quan trọng:** Khi B2B client hoặc audit hỏi *"quote này lấy từ đâu?"*, ref_id link về interview source gốc. Không có ref_id = không có audit trail = không serve được B2B credibility, không pass được audit theo Luật 91/2025.

**Fill ref_id NGAY khi add quote vào CSV.** Không retro-fit sau (sẽ quên).

---

## 4. CSV scope — what goes in, what doesn't

**CSV chỉ chứa structured text findings:**
- Participant profile (`participants.csv`)
- Verbatim quotes + classification (`quotes.csv`)
- Pattern membership
- Confidence levels
- ref_id

**CSV KHÔNG chứa:**
- Photos, videos, audio files (binary)
- Raw interview transcripts (PII, lưu external)
- Consent forms (legal docs, lưu external)
- Field note raw files

Media files (photos pilot tour, audio recordings) lưu ở **external storage** (xem data architecture của MẠCH). CSV chỉ chứa **reference path** nếu cần link, không embed binary.

---

## 5. Freeze gotcha — khi nào full re-render

Quarto `freeze: auto` cache execution outputs theo hash của `.qmd` file, **không theo data file** mà nó import.

**Hệ quả:** Update CSV → chạy `quarto render` → chart vẫn dùng data cũ. Không error, không warning. Silent stale.

**Quy trình đúng khi update CSV:**

```bash
# Option 1: Force ignore freeze
quarto render --no-freeze

# Option 2: Xóa freeze cache trước
rm -rf _freeze/
quarto render
```

**Khi nào cần full re-render:**
- Add/edit rows trong `participants.csv` hoặc `quotes.csv`
- Update `shared/viz_helpers.py`
- Major update `shared/styles.css`

**Khi nào freeze: auto OK (default render đủ):**
- Edit prose trong chapters
- Không đụng data hoặc shared code

---

## 6. Prose-forward writing rules

Stylesheet là prose-forward. Chapter content phải match — nếu không, kết quả inconsistent giữa CSS và content.

**Do:**
- Mỗi quote một `>` blockquote standalone, attribution dạng em-dash bên dưới
- Comparison dùng markdown table
- Findings có narrative bridge (1-2 câu) kết nối các section
- Callout tối đa 2-3/page

**Don't:**
- Quote stacked thành grid 2×2 hoặc cards
- Comparison dạng cards riêng cho từng item
- KPI big numbers ở đầu chapter (n=12 không deserve dashboard)
- Mọi finding bọc trong callout box riêng
- Bold-heavy prose (mỗi câu một đoạn bold)

**Quote format chuẩn:**

```markdown
> "Quote text trực tiếp từ participant, in italic tự động qua CSS."
>
> — **P05**, Gen X, giám đốc
```

Không bọc trong `<div class="quote-card">` hay tương tự. CSS đã handle styling.

**Callout discipline:**

| Loại | Khi dùng | Max per page |
|:--|:--|:--|
| `note` | TL;DR ở đầu page | 1 |
| `tip` | Action item ở cuối | 1 |
| `warning` | Limitation hoặc caveat quan trọng | 1 |

Total tối đa 2-3 callouts/page. Mọi thứ khác chuyển thành prose.

---

## 7. Khi thêm study mới

Đọc CONVENTIONS.md này trước. Mọi convention apply cho study mới.

**Steps:**
1. Tạo `studies/<new-study>/` với folder structure giống study cũ
2. Tạo `data/participants.csv` + `data/quotes.csv` với cùng schema (hoặc extend nếu methodology khác)
3. Copy chapter templates từ existing study, thay TODO với content mới
4. Cập nhật `_quarto.yml` navbar thêm menu cho study mới
5. Update root `index.qmd` thêm link sang study mới
6. Đảm bảo confidence labels + ref_id apply nhất quán

Nếu methodology mới (focus group, ethnography...) cần extra fields trong CSV, document trong study folder's `_meta.yml` hoặc `SCHEMA.md`.

**Không reinvent convention.** Nếu thấy convention hiện tại không fit study mới, propose update CONVENTIONS.md trước, không bypass.
