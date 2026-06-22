# Audit ngôn ngữ — Báo cáo nghiên cứu khách hàng MẠCH (pretour-research-2026)

**Phạm vi:** Báo cáo Quarto đang render (`studies/pretour-research-2026/index.qmd` + `shared/viz_helpers.py` + dữ liệu CSV + CSS).  
**Ngày audit:** 21/06/2026  
**Ràng buộc:** Chỉ đọc — không sửa file nguồn báo cáo.

---

## 1. Đã quét

| File | Vai trò | Render ra HTML? |
|------|---------|-----------------|
| `studies/pretour-research-2026/index.qmd` | Văn xuôi + gọi helper | Có |
| `shared/viz_helpers.py` | Template HTML, nhãn, visual deck | Có |
| `shared/styles.css` | Style (class name tiếng Anh; không text hiển thị) | Có |
| `_quarto.yml` | Cấu hình site (`lang: vi`) | Meta |
| `index.qmd` (gốc repo) | Trang landing tạm | Có (phụ) |
| `studies/pretour-research-2026/data/quotes.csv` | `quote_short`, `context` → panel bằng chứng | Có (qua helper) |
| `studies/pretour-research-2026/data/participants.csv` | Biến số / nhãn nội bộ; một số cột không hiển thị trực tiếp | Một phần (compute) |
| `studies/pretour-research-2026/data/records.csv` | Chỉ dùng đếm `len(records_df)` | Chỉ số |
| `studies/pretour-research-2026/data/hypothesis_tracker.csv` | Tracker nội bộ | Không render hiện tại |
| `studies/pretour-research-2026/STUDY_RULES.md` | Quy tắc dự án | Không render |

**Không quét vào bảng lỗi chính** (không nằm pipeline render): `_archive/**`, `docs/**` (output build), `scripts/**`, `node_modules/**`.

**Ghi chú:** Các hàm dotplot (`render_p1_dotplot_interactive`, …) có trong `viz_helpers.py` nhưng **không được gọi** từ `index.qmd` hiện tại.

---

## 2. Bảng chính

| File | Dòng/Section | Trích nguyên văn | Loại | Nguồn | Đề xuất sửa |
|------|--------------|------------------|------|-------|-------------|
| `index.qmd` | 65 | `visualization` trước giai đoạn pilot tour | A | prose | `minh hoạ dữ liệu` / `đồ hoạ tổng hợp` |
| `index.qmd` | 82, 94, 99, 111, 129, 144, 168, 334, 348, 356, 359 | `concept tour` / `concept MẠCH` / `concept` (nhiều chỗ) | A | prose | `mô hình tour` / `ý tưởng tour MẠCH` (thống nhất một cách gọi) |
| `index.qmd` | 118 | `Record tổng hợp` | A | prose | `Bản ghi tổng hợp` |
| `index.qmd` | 119 | `Report public source` … `PII` | A | prose | `Bản nguồn công khai` … `thông tin nhận dạng cá nhân` |
| `index.qmd` | 128 | `record phỏng vấn` … `report` | A | prose | `bản ghi phỏng vấn` … `báo cáo` |
| `index.qmd` | 173 | `mã hoá` ở P1 | C | prose | `đã gắn chủ đề` / `đã phân loại` |
| `index.qmd` | 189 | `book` | A | prose | `đặt tour` / `tự đăng ký` |
| `index.qmd` | 254 | `cohort 2` | A | prose | `đợt phỏng vấn 2` / `đợt khách 2` |
| `index.qmd` | 270 | `demand đã kiểm chứng` | A | prose | `nhu cầu đã kiểm chứng` |
| `index.qmd` | 286 | `phần mềm hoá lịch trình` | B | prose | Cần anh xác nhận nghĩa: *làm mềm lịch trình* hay *số hoá lịch trình*? (dễ đọc nhầm thành phần mềm) |
| `index.qmd` | 333 | `archetype tạm thời` | A | prose | `kiểu khách tạm thời` |
| `index.qmd` | 335 | `persona` … `expert` … `industry voices` … `partner insight` … `customer persona` | A | prose | `chân dung khách hàng` … `chuyên gia` … `góc nhìn ngành` … `góc nhìn đối tác` … `chân dung khách chính` |
| `index.qmd` | 375 | `report` | A | prose | `báo cáo` |
| `index.qmd` | 376 | `convenience sample` | A | prose | `15 người tự nguyện, không chọn ngẫu nhiên` |
| `index.qmd` | 377 | `foreign audience` | A | prose | `khách nước ngoài` |
| `viz_helpers.py` | 2535 | `Takeaway chính:` | D | template | `Chốt lại:` (`_deck_takeaway`, ~5 slide) |
| `viz_helpers.py` | 2804 | `Takeaway chính:` | D | template | `Chốt lại:` (`_deck_b_footer`, 9 slide IV.B) |
| `viz_helpers.py` | 2898–2901 | Badge `Tần suất` … `participant` / `Evidence` / `Lens` | D | template | `Tần suất` giữ; `người tham gia` / `Câu dẫn chứng` / `Nhóm nói` (`_deck_pattern_meta_box`, ×9 slide B) |
| `viz_helpers.py` | 3084–3087 | Cùng cụm badge (snapshot, không dùng render hiện tại) | D | template | Sửa cùng chỗ nếu bật lại `_deck_pattern_snapshot` |
| `viz_helpers.py` | 2966–2968 | `Quote / record entries` | A,D | template | `Dòng trích dẫn / bản ghi` |
| `viz_helpers.py` | 2968 | `Convenience sample` | A,D | template | `Mẫu tự nguyện (N=15)` |
| `viz_helpers.py` | 2971 | `qualitative convenience sample` | A | template | `mẫu định tính tự nguyện` |
| `viz_helpers.py` | 2981–2986 | `P-code only` / `full compiled record` / `quotes.csv` / `annotation, không loại khỏi mẫu` | A | template | Việt hoá nhãn metric (file 2981–2986) |
| `viz_helpers.py` | 2997 | `Lens khi diễn giải` | A,D | template | `Nhóm nói khi diễn giải` |
| `viz_helpers.py` | 3000 | `Lead user` | A,D | template | `Khách hiểu sâu` |
| `viz_helpers.py` | 3002 | `lens ngành` | A | template | `góc nhìn ngành` (đã Việt; kiểm tra thống nhất) |
| `viz_helpers.py` | 2418, 2439, 2506, 3016–3018, 3055, 3060, 3521, 3570 | `mã hoá` / `chưa mã hoá` / `WTP` / `participant` | C,A | template | `đã phân loại` / `chưa rõ` / `giá chấp nhận được` / `người tham gia` |
| `viz_helpers.py` | 3055 | `Vùng giá được mã hoá cho tour` | C | template | `Vùng giá đã ghi nhận trong dữ liệu` |
| `viz_helpers.py` | 3116 | Subtitle `Phản ứng với concept tour MẠCH` | A | template | Lặp ×9 slide B — `Phản ứng với mô hình tour MẠCH` |
| `viz_helpers.py` | 3137, 3143 | `book` | A | template | `đặt tour` |
| `viz_helpers.py` | 3175, 3179 | `target` / `attitude` | A | template | `nhóm khách nhắm tới` / `thái độ` |
| `viz_helpers.py` | 3181 | `Self-include và self-exclude` | A | template | `tự thấy hợp` và `tự thấy không hợp` |
| `viz_helpers.py` | 3196 | `Visual proof` | A | template | `Hình ảnh minh hoạ rõ` |
| `viz_helpers.py` | 3234 | `visual hậu trường` | A | template | `hình ảnh hậu trường` |
| `viz_helpers.py` | 3245 | `key selling point` | A | template | `điểm bán chính` / `lý do chọn` |
| `viz_helpers.py` | 3252 | `Khoảng cách / logistics` | A | template | `Khoảng cách / lo chuyến đi` (tuỳ ngữ cảnh) |
| `viz_helpers.py` | 3268 | `visual` | A | template | `hình ảnh` |
| `viz_helpers.py` | 3287 | `cohort/pilot` | A | template | `đợt khách` / `chuyến thử` |
| `viz_helpers.py` | 3314 | `check-in` | A | template | `đến chụp ảnh điểm danh` |
| `viz_helpers.py` | 3318–3319 | `Demand chưa kiểm chứng` / `sample` / `lens chuyên môn` | A | template | `Nhu cầu chưa kiểm chứng` / `mẫu` / `góc nhìn chuyên môn` |
| `viz_helpers.py` | 3339 | `demand` | A | template | `nhu cầu` |
| `viz_helpers.py` | 3352 | `Nếu chỉ là bữa ăn logistics` | B | template | Câu cụt, thiếu hệ quả — vd. `Nếu chỉ là bữa ăn phụ… ẩm thực không còn là cửa vào văn hoá` |
| `viz_helpers.py` | 3355 | `Nếu thiếu visual hook` | A,B | template | `Nếu thiếu hình ảnh gây chú ý` (+ bổ sung vế sau nếu cần) |
| `viz_helpers.py` | 3365–3370 | Tiêu đề cột phải `Cách biến thành trải nghiệm` nhưng nội dung là các dòng `Nếu…` (bẫy) | E | template | Đổi tiêu đề → `Rủi ro cần tránh` hoặc đổi nội dung → hành động tích cực (trùng với action grid) |
| `viz_helpers.py` | 3368–3370 | `logistics` / `visual hook` (action cards) | A | template | `phần ăn trong lịch trình` / `hình ảnh gây chú ý` |
| `viz_helpers.py` | 3470 | `Hoặc chỉ đoán là môi trường` | B | template | Mở rộng: `Hoặc chỉ đoán là vấn đề môi trường` |
| `viz_helpers.py` | 3520–3521 | `Sample` / `Mã hoá` / `participant` | A,C,D | template | `Mẫu (N=…)` / `Đã phân loại` / `người tham gia` |
| `viz_helpers.py` | 3589 | `book` | A | template | `đặt tour` |
| `viz_helpers.py` | 3644–3648 | `Archetype` / `qualitative interviews` / `persona` | A | template | `Kiểu khách` / `phỏng vấn định tính` / `chân dung khách` |
| `viz_helpers.py` | 3654 | `persona` (trong takeaway) | A | template | `chân dung khách hàng` |
| `viz_helpers.py` | 3664–3669 | `Concept` (tiêu đề card ×6) | A | template | `Mô hình tour` / `Ý tưởng tour` |
| `viz_helpers.py` | 3690 | `booking thật` | A | template | `đặt tour thật` |
| `viz_helpers.py` | 3692–3693 | `Report` / `anonymize` | A | template | `Báo cáo` / `ẩn danh` |
| `viz_helpers.py` | 2893, 3078, 692+ (dotplot, không render) | `lead user` | A | template | `khách hiểu sâu` |
| `viz_helpers.py` | 692+ (dotplot) | `Chọn một participant để xem trích dẫn` / `industry` (legend) | A | template | Chỉ áp dụng nếu bật dotplot |
| `viz_helpers.py` | 230 | `Lens` (header bảng nội bộ) | A | template | `Nhóm nói` — không render deck hiện tại |
| `viz_helpers.py` | 2254 | Header `Evidence` | A | template | `Câu dẫn chứng` — không render deck hiện tại |
| `quotes.csv` | 8 / Q007 | `—` trong `quote_short` | G | data | Thay bằng `–` hoặc `;` / `,` theo quy ước dự án |
| `quotes.csv` | 17 / Q016 | `—` trong `quote_short` | G | data | Như trên |
| `quotes.csv` | 70–72 / Q069–Q071 | `—` trong `quote_short` hoặc `context` | G | data | Như trên |
| `quotes.csv` | 4 / Q003 | `guide` | A | data | `hướng dẫn viên` |
| `quotes.csv` | 9 / Q008 | `hook` | A | data | `điểm thu hút` |
| `quotes.csv` | 10 / Q009 | `Concept` / `target/segment` | A | data | Việt hoá quote_short |
| `quotes.csv` | 11 / Q010 | `limited audience` | A | data | `nhóm khách hẹp` |
| `quotes.csv` | 12 / Q011 | `soft part` | A | data | `phần nhẹ / phần dễ tiếp cận` |
| `quotes.csv` | 13 / Q012 | `Positioning Vietnamese Studies` | A | data | `Định vị nghiên cứu Việt Nam` |
| `quotes.csv` | 14 / Q013 | `enjoy` | A | data | `thấy thoải mái` / `khó thích thú` |
| `quotes.csv` | 16 / Q015 | `GenZ` | A | data | `thế hệ Z` |
| `quotes.csv` | 18 / Q017 | `(perception)` | A | data | `(cảm nhận)` |
| `quotes.csv` | 20 / Q019 | `single biggest barrier` | A | data | `rào cản lớn nhất` |
| `quotes.csv` | 21 / Q020 | `Target` / `band` | A | data | `Nhóm` / `khoảng tuổi` |
| `quotes.csv` | 26 / Q025 | `skip` / `forced group` | A | data | `bỏ qua` / `bị ép ở lại đoàn` |
| `quotes.csv` | 29 / Q028 | `motif` / `industry view` | A | data | `khuôn mẫu` / `góc nhìn ngành` |
| `quotes.csv` | 31 / Q030 | `Food tour` / `concept` | A | data | `Tour ẩm thực` / `mô hình tour` |
| `quotes.csv` | 33 / Q032 | `Suggest` / `staging tích cực` | A | data | `Đề xuất` / `dàn dựng theo hướng tích cực` |
| `quotes.csv` | 35 / Q034 | `ko trend` / `target` | A | data | `không theo trend` / `nhóm khách` |
| `quotes.csv` | 37 / Q036 | `key selling point` | A | data | `điểm bán chính` |
| `quotes.csv` | 38 / Q037 | `nuanced` | A | data | `có chừng mực` |
| `quotes.csv` | 39 / Q038 | `WTP` | A | data | `Giá chấp nhận` |
| `quotes.csv` | 41 / Q040 | `Target` / `GenZ` | A | data | `Nhóm` / `thế hệ Z` |
| `quotes.csv` | 42 / Q041 | `rate fit` | A | data | `tự đánh giá mức phù hợp` |
| `quotes.csv` | 44 / Q043 | `authenticity` | A | data | `tính chân thực` |
| `quotes.csv` | 45 / Q044 | `strong convert intent` | A | data | `ý định tham gia mạnh` |
| `quotes.csv` | 46 / Q045 | `Gen X` | A | data | `thế hệ X` |
| `quotes.csv` | 48 / Q048 | `Concept` | A | data | `mô hình tour` |
| `quotes.csv` | 50 / Q050 | `H1 strong signal` | A | data | `tín hiệu H1 mạnh` |
| `quotes.csv` | 55 / Q054 | `tag-along` | A | data | `có người dẫn đi cùng` |
| `quotes.csv` | 58–60 / Q057–Q059 | `WTP` | A | data | `Giá chấp nhận` |
| `quotes.csv` | 59 / Q058 | `game hoá` (Latin) | A | data | `trò hoá` / `làm thành trò chơi` |
| `quotes.csv` | 62 / Q061 | `Strong convert intent` | A | data | `Ý định tham gia mạnh` |
| `quotes.csv` | 63 / Q062 | `GenZ-GenY` | A | data | `thế hệ Z–Y` |
| `quotes.csv` | 65 / Q064 | `Logistics` | A | data | `Lo chuyến đi` / `khoảng cách & đi lại` |
| `quotes.csv` | 80 / Q079 | `search TikTok` | A | data | `tìm trên TikTok` |
| `quotes.csv` | 85–86 / Q084–Q085 | `hook` / `video` | A | data | `điểm thu hút` (giữ TikTok nếu là tên app) |
| `quotes.csv` | 83 / Q083 | `Local` | A | data | `Người địa phương thật` |
| `quotes.csv` | *context* (≈85 dòng) | Tiếng Anh lẫn: `concept card`, `Reaction concept`, `target audience`, `re-enactment`, `staging`, `WTP`, `convert intent`, `Phần 2 Concept`, `familiarity-bias`, `participant`, v.v. | A | data | Việt hoá cột `context` khi hiển thị trong panel (người đọc thấy dưới trích dẫn) |
| `participants.csv` | 7 / P06 `note` | `transcript` … `reading likely` … `FLAG` (nội bộ) | A | data | Không hiển thị deck; sửa nếu sau này expose |
| `participants.csv` | 2–15 `convert_condition` | Nhiều cụm EN: `expert guide`, `credentials`, `human-centered`, `hook`, `target/segment`, `soft elements`, `Vietnamese Studies`, `anti-tour`, `local immersion`, `tag-along`, `visual proof`, `game hoá`, `logistics`, v.v. | A | data | Chỉ metadata; Việt hoá nếu đưa ra báo cáo |

*Từ `tour`, `pilot`, `P-code`, `TikTok`, tên riêng (Nam Định, Sapa…) — giữ hoặc xử lý tuỳ quy ước; không liệt kê hết.*

---

## 3. Sửa một lần ở template

| Nhãn / cụm lặp | File + vị trí định nghĩa | Ước lượng chỗ bị ảnh hưởng |
|----------------|---------------------------|----------------------------|
| **`Takeaway chính:`** | `shared/viz_helpers.py` — `_deck_takeaway()` L2531–2536; `_deck_b_footer()` L2797–2805 | **~14** thẻ (9 slide IV.B + 5 slide IV.A/C/D/V) |
| **Badge meta IV.B:** `Tần suất` / `Evidence` / `Độ tin cậy` / `Lens` + giá trị `… participant` | `_deck_pattern_meta_box()` L2880–2902 | **9** slide (IV.B.1–IV.B.9) |
| **`Quote / record entries`** | `render_cover_stats()` L2966; `render_sample_deck_visual()` L2982 | **2** vùng |
| **`Convenience sample`** + note `qualitative convenience sample` | `render_cover_stats()` L2968–2971 | **1** cover |
| **`Lead user`** (bar chart) | `render_sample_deck_visual()` L3000 | **1** |
| **`Lens khi diễn giải`** | `render_sample_deck_visual()` L2997 | **1** |
| **`mã hoá` / `chưa mã hoá` / `WTP` / `participant`** trong bar & note | `_deck_bool_label`, `_deck_wtp_band_counts`, `render_decision_deck_visual`, `render_sustainability_deck_visual` | **~6** vùng số liệu |
| **Subtitle lặp** `Phản ứng với concept tour MẠCH` | Mỗi `render_b*_visual()` | **9** slide |
| **`Sample` / `Mã hoá` / `Archetype` / `persona` / `qualitative interviews`** | `render_archetype_deck_visual()` L3642–3654 | **1** slide IV.D |
| **`Report` / `anonymize` / `booking`** | `render_limitations_visual()` L3690–3693 | **1** slide V.2 |

**Khuyến nghị kỹ thuật:** Tạo hằng số nhãn (vd. `LABEL_TAKEAWAY = "Chốt lại:"`) ở đầu `viz_helpers.py` để tránh sót khi sửa.

---

## 4. Cần anh quyết

### 4.1 [TÍN NGƯỠNG] — chỉ lỗi ngôn ngữ, không đổi giọng nội dung

| File | Dòng/Section | Trích nguyên văn | Vấn đề | Đề xuất (ngôn ngữ) |
|------|--------------|------------------|--------|-------------------|
| `index.qmd` | IV.B.9 (302–303) | `Đạo Mẫu` … `lớp trải nghiệm sâu` | Tiếng Việt ổn; không đổi giọng | — |
| `viz_helpers.py` | `render_b9_visual` L3381–3387 | `Đạo Mẫu` … `Không chỉ là Đạo Mẫu` | OK nội dung | Chỉ sửa nếu còn EN lẫn (không thấy) |
| `quotes.csv` | Q021, Q032, Q050, Q061, Q070 | `canh hầu`, `hầu đồng`, `thờ Mẫu`, `Đạo Mẫu`, `Phật giáo` | Một số `context`/`quote_short` còn EN: `Reaction concept (canh hầu interest)`, `staging tích cực`, `H1 strong signal` | Việt hoá phần EN; **giữ** thuật ngữ tín ngưỡng |
| `quotes.csv` | Q070 `context` | `caveat data có chủ đích` | Jargon EN trong ghi chú nội bộ hiển thị panel | `ghi chú dữ liệu có chủ đích` |
| `viz_helpers.py` | `render_b4_visual` L3218 | `tín ngưỡng và thực hành văn hoá` | Câu đủ nghĩa | — |
| `viz_helpers.py` | `render_concept_advantage_visual` L3668 | `Tín ngưỡng` … `kể an toàn` | OK | — |

### 4.2 Nhập nhằng nghĩa / cần xác nhận người viết

| Chỗ | Câu hỏi |
|-----|---------|
| `index.qmd` L286 | **「phần mềm hoá lịch trình」** — ý là *làm mềm* lịch trình (ẩm thực làm cửa vào) hay *số hoá* / phần mềm? |
| `viz_helpers.py` IV.B.8 L3365 vs L3351–3355 | Tiêu đề cột **「Cách biến thành trải nghiệm」** nhưng nội dung là **「Nếu chỉ là bữa ăn logistics」** — đây là lỗi copy-paste tiêu đề hay cố ý? |
| `index.qmd` L282 vs slide B8 | Prose nói ẩm thực là **điểm vào**; slide phải liệt kê **rủi ro** — có cần thêm đoạn prose về rủi ro cho khớp slide? |
| Thuật ngữ **`pilot`** | Dùng rộng trong báo cáo (cho phép giữ như thuật ngữ dự án?) hay Việt hoá thành *chuyến thử nghiệm*? |
| **`P1`–`P6`, `S1`, `S2`, `H1`** | Mã pattern — giữ nguyên hay thêm chú thích tiếng Việt lần đầu? |

---

## 5. Tóm tắt theo loại

| Loại | Số lượng ước lượng | Ưu tiên |
|------|-------------------|---------|
| **A** Tiếng Anh lẫn | ~120+ (prose ~25, template ~60, data ~40+ quote/context) | Cao — template trước, prose & CSV sau |
| **B** Câu cụt / dễ nhầm | ~5 | Trung — cần anh quyết 2 chỗ (mềm hoá / logistics) |
| **C** Jargon `mã hoá` | ~15 | Trung — gom ở helper |
| **D** Nhãn lặp EN/VI | ~5 nhóm template | **Cao** — sửa một lần, ~14–20 chỗ |
| **E** Lệch tiêu đề–nội dung | 1 (IV.B.8) | Cao |
| **F** Em-dash | 0 prose; **5** dòng `quotes.csv` hiển thị panel | Thấp–trung |
| **G** [TÍN NGƯỠNG] | ~8 dòng (chủ yếu EN trong context quote) | Thấp — chỉ Việt hoá EN |

---

*File này là kết quả audit duy nhất được tạo; không có thay đổi nào trên file báo cáo nguồn.*
