# STUDY_RULES — Pre-Tour Research 2026 (MẠCH)

Persistent build rules cho `studies/pretour-research-2026/`.
**Đọc [CONVENTIONS.md](../../CONVENTIONS.md) trước, rồi file này khi sửa `.qmd` / `.csv` của study.** Rule bền vững; task cụ thể đi qua prompt (mục 9).

---

## 1. Bối cảnh

Nghiên cứu định tính pre-tour cho pilot Nam Định 7/2026 (MẠCH — du lịch trải nghiệm văn hoá + Insight-as-a-Service). 14 phỏng vấn semi-structured. Output: Quarto report cho các team nội bộ (Tour Design, Content, Finance, Data, Leadership). **Đây KHÔNG phải sản phẩm B2B** — xem mục 8.

## 2. Rule #1 — Compute, đừng gõ tay

`data/participants.csv` + `data/quotes.csv` = **single source of truth duy nhất.**

- MỌI con số (count, %, occurrence) và MỌI quote trong `.qmd` phải được **compute từ CSV trong code chunk**, KHÔNG hardcode.
- Lý do: bản report PDF trước sai hàng loạt vì gõ tay số liệu (nhầm spend với giá tour, gán sai quê quán, đếm lệch 5 vs 6). Compute thì lớp lỗi đó không xảy ra được.
- Nếu một con số không compute được từ CSV → nó **chưa được phép xuất hiện** trong report; bổ sung data vào CSV trước.

Chi tiết confidence labels và mẫu số: [CONVENTIONS.md](../../CONVENTIONS.md) mục 2.

## 3. Sample — LOCKED (quyết định C)

- **N = 14.** Không ngoại lệ. (`chua_tung` = 8, `da_tung` = 6.)
- **KHÔNG tách customer/expert để tính %.** Tất cả 14 người vào mẫu số.
- Pattern occurrence = `count(distinct pid)` theo `pattern_id`, **trên mẫu số 14** (hoặc trên subgroup kinh nghiệm khi pattern đặc thù nhóm). **Luôn ghi rõ mẫu số**, vd "9/14" hoặc "5/8 chưa-từng".
- "Góc nhìn chuyên môn/ngành" là **TAG chú thích** (cột `lens`), KHÔNG phải lý do loại ai khỏi %.
- **Nhưng phải DÙNG tag đó khi diễn giải:** nếu một pattern/signal chủ yếu do người `lens=industry` nói (vd "tour này cho người nước ngoài"), ghi rõ **"(thiên về góc nhìn ngành)"** — đừng nhầm ý kiến chuyên môn thành demand của khách thật.

## 4. Schema CSV (authoritative — đừng đổi cột tuỳ tiện)

### participants.csv
| cột | giá trị | ghi chú |
|---|---|---|
| `pid` | P01…P14 | ID cố định — ổn định, KHÔNG renumber (quotes link theo `pid`). Hiển thị sắp theo `convert_type` qua compute (vd `participants_table()` trong `shared/viz_helpers.py`), KHÔNG sắp lại trong CSV. |
| `experience` | `da_tung` / `chua_tung` | thay cột `group` cũ — đây là split có ý nghĩa |
| `lens` | `customer` / `industry` / `lead_user` | **annotation only**, KHÔNG filter % |
| `age_group` | text | |
| `residence` | `mien_bac` / `mien_trung` / `mien_nam` | vùng sinh sống hiện tại — **CHỈ region-level, KHÔNG ghi city cụ thể** (anonymization). Source được phép: (a) participant tự nêu trong transcript, HOẶC (b) MẠCH team confirm từ interview/recruitment metadata. Abstraction: Hà Nội/Hải Phòng/etc. → `mien_bac`; Đà Nẵng/Huế/etc. → `mien_trung`; HCM/Cần Thơ/etc. → `mien_nam`. Để rỗng nếu cả 2 source không có. Note ghi source ("transcript" / "MẠCH team confirm + date"). |
| `occupation` | text | |
| `convert_type` | `true_target` / `conditional` / `passive` / `harder` / `future` / `non_target` | |
| `convert_condition` | text | điều kiện để convert |
| `decision_style` | text | vd family-led, self-directed |
| `travel_spend_range` | text | **mức chi du lịch THẬT** (đổi tên từ `travel_budget_range`) |
| `acceptable_tour_price` | text | **giá tour CHẤP NHẬN ĐƯỢC** — KHÁC spend, đừng gộp |
| `note` | text | |

### quotes.csv
| cột | ghi chú |
|---|---|
| `quote_id` | Q001… |
| `pid` | link tới participant |
| `pattern_id` | dùng ID ở mục 5 (P1…S2); để rỗng nếu chỉ là context |
| `theme` / `subtheme` | dùng tên taxonomy chuẩn |
| `quote_full` | nguyên văn (cho quote-bank) |
| `quote_short` | bản rút gọn cho copy |
| `context` | bối cảnh, KHÔNG nhồi chi tiết nhận dạng |
| `confidence_level` | `cao` / `trung_binh` / `som` / `hypothesis` |
| `ref_id` | nguồn (PDF + trang) — format: [CONVENTIONS.md](../../CONVENTIONS.md) mục 3 |

## 5. Taxonomy findings — LOCKED (tên & loại)

Định nghĩa pattern là LOCKED (tên + nghĩa KHÔNG đổi). **Tên hiển thị + tier confidence (Cao / Trung bình / …):** [`shared/viz_helpers.py`](../../shared/viz_helpers.py) → `PATTERN_META` và `CONFIDENCE_TIERS` — đây là nguồn render trong `findings.qmd`.

Nhãn confidence là đánh giá COHORT 1 đã reconcile với evidence compute từ CSV (Rule #1); rà lại mỗi cohort qua Hypothesis Tracker (mục 10). Số occurrence (X/14) compute trong findings, KHÔNG hardcode.

**Caveats bắt buộc khi báo cáo (không nằm trong code):**

| ID | Caveat |
|:---|:---|
| **P1** | Đa số nguồn là khách thật, không phải artifact ngành. |
| **P2** | ~5 nguồn + **2 ngoại lệ** thoải mái đi một mình (P03, P07) — PHẢI ghi kèm khi báo cáo. |
| **P3** | Nhiều nguồn (~10) nhưng **TRÁI CHIỀU** (self-include vs self-exclude). TB vì thiếu đồng thuận, KHÔNG vì ít nguồn. |
| **P5** | PATTERN (rào cản điểm đến), KHÔNG phải signal. |
| **P6** | Chỉ 1 nguồn (P05); watch-item cohort 2. KHÔNG gán "gốc Nam Định". |
| **H1** | Tín ngưỡng **BROAD** (Phật + Đạo Mẫu + …), KHÔNG chỉ Đạo Mẫu. Gender-neutral; TUYỆT ĐỐI KHÔNG "phụ nữ tâm linh". Quan tâm broad ≠ quan tâm tour Đạo Mẫu cụ thể (P01 skeptical concept). |
| **S1** | Phỏng đoán về nhóm **VẮNG MẶT** (khách nước ngoài không trong mẫu) → claim "Tây muốn tour" CHƯA kiểm được. Thiên góc nhìn ngành. KHÔNG nâng "trung bình". |
| **S2** | SIGNAL có action pilot; thiên góc nhìn ngành; KHÔNG phải data gap. |

## 6. Terminology (immutable)

- Dùng **"khách quan tâm tín ngưỡng"**, KHÔNG "phụ nữ tâm linh".
- KHÔNG gán "gốc Nam Định" (hay bất kỳ quê quán nào) cho participant trừ khi có nguồn xác nhận trong data.
- Luôn tách **mức chi du lịch (spend)** ≠ **giá tour chấp nhận được (willingness-to-pay)**.
- **Pattern** = rào cản lặp lại; **Signal** = cơ hội/hướng cần explore. Đừng lẫn.
- Glossary: Đạo Mẫu = tín ngưỡng thờ Mẫu Việt Nam; hầu đồng = nghi lễ lên đồng.

## 7. Audiences — mỗi file phục vụ ai

- `overview.qmd` — tổng quan (mọi người)
- `methodology.qmd` — phương pháp + limitations + confidence levels
- `participants.qmd` — 14 deep dives (P01→P14, order theo convert likelihood)
- `findings.qmd` — patterns + signals (computed)
- `quote-bank.qmd` — quote search (itables)
- `audiences/leadership.qmd` — quyết định founder (lock segment pilot; pilot 7/2026 = trust-building event, không phải tour đầu tiên)
- `audiences/tour-design.qmd` · `content.qmd` · `finance.qmd` · `data.qmd`

## 8. Privacy / internal vs external

- Report này **internal-only**, dùng P-code.
- BẤT KỲ output ra ngoài MẠCH (B2B/đối tác) phải **anonymize** + tuân thủ khung consent/pháp lý (Luật 91/2025/QH15; xem docs governance của dự án — FPIC, khung pháp lý xử lý dữ liệu khách hàng).
- KHÔNG trộn P-code với tên thật trong bất kỳ file commit nào. Crosswalk PII: [CONVENTIONS.md](../../CONVENTIONS.md) mục 4.

## 9. File này vs prompt

- **STUDY_RULES.md (file này)** = rule bền vững study. Không bỏ số liệu cụ thể hay trạng thái task vào đây.
- **Prompt** = task từng lần, vd:
  - "Extract P01–P14 từ 2 PDF vào `participants.csv` + `quotes.csv` theo schema mục 4. Tag `lens` đúng, tách spend vs giá-tour."
  - "Dựng section `P1` trong `findings.qmd`: compute occurrence từ `quotes.csv` (count distinct pid /14), pull 2 quote `confidence=cao`."

## 10. Hypothesis Tracker (Bayesian accumulation)

`data/hypothesis_tracker.csv` — sống qua mọi cohort, operationalize tích luỹ Bayesian (Tour 1 → 2 → pilot).

- **KHÔNG build/populate ở phase skeleton** — chưa có data để track. Tạo header-only SAU khi cohort 1 extract xong; mỗi cohort thêm một batch row.
- Một row = trạng thái một finding tại một cohort.
- Schema: `finding_id, cohort, status, evidence_delta, confidence_after, date, note`
  - `finding_id`: P1…S2 (taxonomy mục 5)
  - `status`: confirm / challenge / new / unchanged
  - `confidence_after`: cao / trung_binh / som / hypothesis — mức SAU cohort này
- Mỗi cohort phải update file này; findings.qmd có thể render lịch sử confidence từng finding từ đây (compute, không gõ tay — Rule #1).
