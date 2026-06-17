"""
viz_helpers.py — Compute helpers for MẠCH pretour-research-2026.

Rule #1: số trong báo cáo compute từ CSV, KHÔNG hardcode.
- Total participants = len(participants_df).
- Confidence pattern lấy từ PATTERN_META (sync STUDY_RULES.md mục 5; caveats báo cáo trong STUDY_RULES),
  KHÔNG lấy từ field `confidence_level` của quote (field đó là per-quote, mơ hồ
  để derive pattern-level).
- P-code only. `OCCUPATION_GENERALIZED` đã bỏ tên công ty/tổ chức.

Báo cáo là prose + markdown table. Không có chart.
"""

import html
import json
import pandas as pd
from pathlib import Path

CONFIDENCE_TIERS = ("Cao", "Trung bình", "Tín hiệu sớm", "Hypothesis")
_TIER_ORDER = {t: i for i, t in enumerate(CONFIDENCE_TIERS)}

CONVERT_TYPE_ORDER = (
    "true_target", "conditional", "passive", "harder", "future", "non_target"
)
_CONVERT_ORDER = {c: i for i, c in enumerate(CONVERT_TYPE_ORDER)}

PATTERN_META = {
    "P1": {
        "name": "Thiết kế tour quá thụ động",
        "confidence": "Cao",
        "note": (
            "Hình thức quá thụ động, không phải nội dung quá sâu. "
            "Giảm liều, tăng hoạt động tự tay làm."
        ),
    },
    "P2": {
        "name": "Phụ thuộc người đồng hành",
        "confidence": "Cao",
        "note": (
            "Rào cản là thiếu đúng người đi cùng, không phải từ chối tour. "
            "Cần mời theo nhóm thay vì để từng người tự đăng ký."
        ),
    },
    "P3": {
        "name": "Nhận diện phân khúc: 'tour cho người khác, không hẳn tôi'",
        "confidence": "Trung bình",
        "note": (
            "Phân hóa rõ giữa người tự nhận phù hợp và tự loại. Phân khúc "
            "là tư duy, không phải tuổi. Truyền thông nhắm vào thái độ."
        ),
    },
    "P4": {
        "name": "Cảnh giác văn hoá \"dàn dựng giả\"",
        "confidence": "Trung bình",
        "note": (
            "3 nhóm phản ứng khác nhau. Cần nói rõ 'nghi lễ thật có khách "
            "chứng kiến' trước khi vào lễ."
        ),
    },
    "P5": {
        "name": "Uy tín điểm đến (Nam Định)",
        "confidence": "Trung bình",
        "note": (
            "Ba bản chất khác nhau: thương hiệu, địa lý, góc ngành. "
            "Mỗi bản chất cần cách giải riêng."
        ),
    },
    "P6": {
        "name": "Quá quen, không còn nhu cầu khám phá",
        "confidence": "Tín hiệu sớm",
        "note": (
            "Tín hiệu đơn lẻ. Cần theo dõi ở đợt phỏng vấn tiếp theo "
            "trước khi kết luận."
        ),
    },
    "H1": {
        "name": "Khách quan tâm tín ngưỡng",
        "confidence": "Hypothesis",
        "note": (
            "Hứng thú thật nhưng phạm vi rộng, từ Phật giáo đến Đạo Mẫu. "
            "Không định vị là 'tour phụ nữ tâm linh.'"
        ),
    },
    "S1": {
        "name": "Tiềm năng khách nước ngoài",
        "confidence": "Hypothesis",
        "note": (
            "Phỏng đoán của người Việt về nhóm vắng mặt. Cần dành suất "
            "pilot cho khách nước ngoài để kiểm chứng trực tiếp."
        ),
    },
    "S2": {
        "name": "Ẩm thực là đòn bẩy mềm",
        "confidence": "Trung bình",
        "note": (
            "Tín hiệu có thể khai thác ngay. Ẩm thực có thể là điểm vào "
            "mềm cho người chưa sẵn sàng với nội dung văn hóa nặng hơn."
        ),
    },
}

OCCUPATION_GENERALIZED = {
    "P01": "Chức danh không nêu (đi công tác)",
    "P02": "Trợ lý giám đốc",
    "P03": "Giảng viên đại học",
    "P04": "Bán quần áo tự do",
    "P05": "Nhân viên văn phòng",
    "P06": "Nhân viên ngành xuất khẩu",
    "P07": "Ngành thời trang (cựu ngành tour outbound)",
    "P08": "Nhân sự ngân hàng",
    "P09": "Sales xuất khẩu",
    "P10": "Giám đốc (cựu giám đốc xuất khẩu)",
    "P11": "NGO — phát triển cộng đồng",
    "P12": "Nghỉ hưu",
    "P13": "Giảng viên đại học (cựu agency du lịch)",
    "P14": "Founder startup du lịch (chuyển từ CSR)",
    "P15": "Du học sinh",
}


# ----------------------------------------------------------------- data load

def load_study_data(study_dir):
    """Load participants.csv + quotes.csv. Assert shape cohort 1."""
    study_dir = Path(study_dir)
    participants = pd.read_csv(study_dir / "data" / "participants.csv")
    quotes = pd.read_csv(study_dir / "data" / "quotes.csv")
    return participants, quotes


def load_records_data(study_dir):
    """Load full compiled records.csv."""
    study_dir = Path(study_dir)
    return pd.read_csv(study_dir / "data" / "records.csv")


# ----------------------------------------------------------------- core compute

def pattern_occurrence(pattern_id, quotes_df, participants_df):
    """Distinct pid có ≥1 quote thuộc pattern. Mẫu số = len(participants_df)."""
    total = len(participants_df)
    pids = sorted(quotes_df.loc[quotes_df["pattern_id"] == pattern_id, "pid"].unique())
    return {
        "pattern_id": pattern_id,
        "count": len(pids),
        "total": total,
        "pids": pids,
        "label": f"{len(pids)}/{total}",
    }


def pattern_lens_breakdown(pattern_id, quotes_df, participants_df):
    """Lens distribution của pids có pattern. industry_leaning = industry >= customer."""
    pids = quotes_df.loc[quotes_df["pattern_id"] == pattern_id, "pid"].unique()
    sub = participants_df[participants_df["pid"].isin(pids)]
    counts = sub["lens"].value_counts().to_dict()
    customer = int(counts.get("customer", 0))
    industry = int(counts.get("industry", 0))
    lead_user = int(counts.get("lead_user", 0))
    return {
        "pattern_id": pattern_id,
        "customer": customer,
        "industry": industry,
        "lead_user": lead_user,
        "industry_leaning": industry >= customer and (industry + customer) > 0,
    }


def quotes_for(pattern_id, quotes_df, participants_df, lens=None, limit=None):
    """Quotes của một pattern, optional filter lens, optional limit."""
    df = quotes_df[quotes_df["pattern_id"] == pattern_id].copy()
    if lens is not None:
        pids = participants_df.loc[participants_df["lens"] == lens, "pid"].tolist()
        df = df[df["pid"].isin(pids)]
    df = df[["pid", "quote_short", "ref_id", "quote_full"]]
    if limit is not None:
        df = df.head(limit)
    return df.reset_index(drop=True)


# ----------------------------------------------------------------- markdown render

def _md_table(headers, rows):
    """Render pipe-delimited markdown table. Escape `|` in cells."""
    def esc(x):
        s = "" if x is None else str(x)
        return s.replace("|", "\\|").replace("\n", " ")
    out = ["| " + " | ".join(esc(h) for h in headers) + " |"]
    out.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)


def _format_lens_cell(b):
    parts = []
    if b["customer"]:
        parts.append(f"{b['customer']} KH")
    if b["industry"]:
        parts.append(f"{b['industry']} ngành")
    if b["lead_user"]:
        parts.append(f"{b['lead_user']} lead")
    cell = " / ".join(parts) if parts else "—"
    if b["industry_leaning"]:
        cell += " (thiên góc nhìn ngành)"
    return cell


def patterns_summary_table(quotes_df, participants_df):
    """All patterns + signals + hypothesis: Pattern | X/N | Lens | Confidence | Note.
    Sort: tier confidence (Cao→TB→Sớm→Hypothesis), rồi occurrence desc.
    """
    rows = []
    for pid, meta in PATTERN_META.items():
        occ = pattern_occurrence(pid, quotes_df, participants_df)
        lens = pattern_lens_breakdown(pid, quotes_df, participants_df)
        rows.append((
            _TIER_ORDER[meta["confidence"]],
            -occ["count"],
            f"{pid} — {meta['name']}",
            occ["label"],
            _format_lens_cell(lens),
            meta["confidence"],
            meta["note"] or "—",
        ))
    rows.sort(key=lambda r: (r[0], r[1]))
    body = [r[2:] for r in rows]
    return _md_table(
        ["Pattern", "Số người", "Lens", "Độ tin cậy", "Điểm chính"], body
    )


def render_pattern_interactive(pid_pattern, interpretation_prose, quotes_df, participants_df):
    """
    Render một pattern section dưới dạng HTML interactive:
    - Prose block (truyền vào qua interpretation_prose)
    - Confidence tier overview (9 patterns, active = pid_pattern hiện tại)
    - Quote explorer: click vào quote để expand full text
    Trả về HTML string. Compute mọi thứ từ quotes_df + participants_df.
    """
    if pid_pattern not in PATTERN_META:
        raise ValueError(f"Unknown pattern id: {pid_pattern!r}")

    block_id = f"pattern-interactive-{html.escape(pid_pattern, quote=True)}"
    active_meta = PATTERN_META[pid_pattern]

    _DISPLAY_ZONES = [
        ("Tin cậy cao",   ("Cao",)),
        ("Trung bình",    ("Trung bình",)),
        ("Cần thêm data", ("Tín hiệu sớm", "Hypothesis")),
    ]
    tier_cards = []
    for zone_label, zone_tiers in _DISPLAY_ZONES:
        pattern_rows = []
        zone_patterns = [
            (pid, meta) for pid, meta in PATTERN_META.items()
            if meta["confidence"] in zone_tiers
        ]
        zone_patterns.sort(
            key=lambda item: (
                -pattern_occurrence(item[0], quotes_df, participants_df)["count"],
                item[0],
            )
        )
        for pid, meta in zone_patterns:
            occ = pattern_occurrence(pid, quotes_df, participants_df)
            active_class = " is-active" if pid == pid_pattern else ""
            badge = ""
            if len(zone_tiers) > 1:
                badge_text = "tín hiệu" if meta["confidence"] == "Tín hiệu sớm" else "hypothesis"
                badge = f'<span class="pill-badge">{html.escape(badge_text)}</span>'
            pattern_rows.append(
                f'<div class="pattern-pill{active_class}" data-pattern-id="{html.escape(pid, quote=True)}">'
                f'<div class="pattern-pill__id">{html.escape(pid)}</div>'
                f'<div class="pattern-pill__body">'
                f'<div class="pattern-pill__name">{html.escape(meta["name"])}{badge}</div>'
                f'<div class="pattern-pill__meta">{html.escape(occ["label"])} participants</div>'
                f'</div>'
                f'</div>'
            )
        tier_cards.append(
            f'<section class="tier-card">'
            f'<h4>{html.escape(zone_label)}</h4>'
            f'<div class="tier-card__patterns">{"".join(pattern_rows)}</div>'
            f'</section>'
        )

    quote_rows = quotes_df[quotes_df["pattern_id"] == pid_pattern].copy()
    quote_rows = quote_rows.merge(
        participants_df[["pid", "lens"]],
        on="pid",
        how="left",
    )
    quote_rows = quote_rows.sort_values(["pid", "quote_id"])

    quote_cards = []
    for _, row in quote_rows.iterrows():
        pid = "" if pd.isna(row.get("pid")) else str(row["pid"])
        lens = "" if pd.isna(row.get("lens")) else str(row["lens"])
        confidence = (
            "" if pd.isna(row.get("confidence_level"))
            else str(row["confidence_level"])
        )
        quote_short = (
            "" if pd.isna(row.get("quote_short"))
            else str(row["quote_short"])
        )
        quote_full = (
            "" if pd.isna(row.get("quote_full"))
            else str(row["quote_full"])
        )
        ref_id = "" if pd.isna(row.get("ref_id")) else str(row["ref_id"])
        quote_cards.append(
            f'<article class="quote-card" data-pid="{html.escape(pid, quote=True)}">'
            f'<button class="quote-card__summary" type="button" aria-expanded="false">'
            f'<span class="quote-card__quote-text">"{html.escape(quote_short or quote_full)}"</span>'
            f'<span class="quote-card__toggle" aria-hidden="true">\u2193</span>'
            f'<span class="quote-card__meta">'
            f'<strong>{html.escape(pid)}</strong>'
            f'<span>{html.escape(lens)}</span>'
            f'<span class="confidence-badge">{html.escape(confidence)}</span>'
            f'</span>'
            f'</button>'
            f'<div class="quote-card__full" hidden>'
            f'<p class="quote-card__full-text">{html.escape(quote_full)}</p>'
            f'<p class="quote-card__ref">{html.escape(ref_id)}</p>'
            f'</div>'
            f'</article>'
        )

    if not quote_cards:
        quote_cards.append(
            '<p class="quote-empty">No quotes tagged for this pattern yet.</p>'
        )

    _occ_label = html.escape(
        pattern_occurrence(pid_pattern, quotes_df, participants_df)["label"]
    )
    _confidence = html.escape(active_meta["confidence"])
    return (
        f'<section id="{block_id}" class="pattern-interactive"'
        f' data-active-pattern="{html.escape(pid_pattern, quote=True)}">\n'
        f"<style>\n"
        f"    #{block_id} {{\n"
        f"        display: grid;\n"
        f"        gap: 1rem;\n"
        f"        margin: 1.5rem 0;\n"
        f"        color: var(--color-text-primary);\n"
        f"    }}\n"
        f"    #{block_id} .pattern-interactive__intro,\n"
        f"    #{block_id} .tier-card,\n"
        f"    #{block_id} .quote-card {{\n"
        f"        background: var(--color-background-primary);\n"
        f"        border: 1px solid var(--color-border-primary);\n"
        f"        border-radius: 0.9rem;\n"
        f"        box-shadow: var(--shadow-sm);\n"
        f"    }}\n"
        f"    #{block_id} .pattern-interactive__intro {{\n"
        f"        padding: 1rem 1.15rem;\n"
        f"    }}\n"
        f"    #{block_id} .pattern-interactive__intro p:last-child {{\n"
        f"        margin-bottom: 0;\n"
        f"    }}\n"
        f"    #{block_id} .pattern-interactive__header {{\n"
        f"        display: flex;\n"
        f"        flex-wrap: wrap;\n"
        f"        gap: 0.5rem;\n"
        f"        align-items: baseline;\n"
        f"        justify-content: space-between;\n"
        f"    }}\n"
        f"    #{block_id} .pattern-interactive__header h3,\n"
        f"    #{block_id} .tier-card h4 {{\n"
        f"        margin: 0;\n"
        f"    }}\n"
        f"    #{block_id} .pattern-interactive__meta {{\n"
        f"        color: var(--color-text-secondary);\n"
        f"        font-size: 0.92rem;\n"
        f"    }}\n"
        f"    #{block_id} .pid-ref {{\n"
        f"        cursor: pointer;\n"
        f"        font-weight: 700;\n"
        f"        text-decoration: underline;\n"
        f"        text-decoration-style: dotted;\n"
        f"        text-underline-offset: 0.18em;\n"
        f"    }}\n"
        f"    #{block_id} .pid-ref.is-active {{\n"
        f"        background: var(--color-background-secondary);\n"
        f"        border-radius: 0.25rem;\n"
        f"    }}\n"
        f"    #{block_id} .tier-grid {{\n"
        f"        display: grid;\n"
        f"        gap: 0.75rem;\n"
        f"        grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));\n"
        f"    }}\n"
        f"    #{block_id} .tier-card {{\n"
        f"        padding: 0.9rem;\n"
        f"    }}\n"
        f"    #{block_id} .tier-card__patterns {{\n"
        f"        display: grid;\n"
        f"        gap: 0.5rem;\n"
        f"        margin-top: 0.75rem;\n"
        f"    }}\n"
        f"    #{block_id} .pattern-pill {{\n"
        f"        display: grid;\n"
        f"        grid-template-columns: auto 1fr;\n"
        f"        gap: 0.65rem;\n"
        f"        padding: 0.6rem;\n"
        f"        border: 0.5px solid var(--color-border-primary);\n"
        f"        border-radius: 0.7rem;\n"
        f"        background: var(--color-background-secondary);\n"
        f"    }}\n"
        f"    #{block_id} .pattern-pill.is-active {{\n"
        f"        border: 1.5px solid var(--color-border-primary);\n"
        f"        background: var(--color-background-secondary);\n"
        f"        font-weight: 500;\n"
        f"    }}\n"
        f"    #{block_id} .pattern-pill__id {{\n"
        f"        font-weight: 800;\n"
        f"    }}\n"
        f"    #{block_id} .pattern-pill__name {{\n"
        f"        color: var(--color-text-secondary);\n"
        f"    }}\n"
        f"    #{block_id} .pattern-pill.is-active .pattern-pill__name {{\n"
        f"        color: var(--color-text-primary);\n"
        f"    }}\n"
        f"    #{block_id} .pattern-pill__meta {{\n"
        f"        color: var(--color-text-secondary);\n"
        f"        font-size: 0.85rem;\n"
        f"    }}\n"
        f"    #{block_id} .pill-badge {{\n"
        f"        display: inline-block;\n"
        f"        font-size: 0.72rem;\n"
        f"        padding: 0.05rem 0.3rem;\n"
        f"        border-radius: 999px;\n"
        f"        border: 1px solid var(--color-border-primary);\n"
        f"        margin-left: 0.35rem;\n"
        f"        vertical-align: middle;\n"
        f"        font-weight: 400;\n"
        f"    }}\n"
        f"    #{block_id} .quote-explorer {{\n"
        f"        display: grid;\n"
        f"        gap: 0.75rem;\n"
        f"    }}\n"
        f"    #{block_id} .quote-card {{\n"
        f"        overflow: hidden;\n"
        f"        background: var(--color-background-primary);\n"
        f"        border: 0.5px solid var(--color-border-primary);\n"
        f"        border-radius: 0.9rem;\n"
        f"        transition: background 0.15s ease, border-color 0.15s ease, opacity 0.15s ease;\n"
        f"    }}\n"
        f"    #{block_id} .quote-card:has(button[aria-expanded='true']) {{\n"
        f"        background: var(--color-background-secondary);\n"
        f"    }}\n"
        f"    #{block_id} .quote-card.is-muted {{\n"
        f"        opacity: 0.5;\n"
        f"    }}\n"
        f"    #{block_id} .quote-card.is-highlighted {{\n"
        f"        border: 1.5px solid var(--warn);\n"
        f"        opacity: 1;\n"
        f"    }}\n"
        f"    #{block_id} .quote-card__summary {{\n"
        f"        width: 100%;\n"
        f"        display: grid;\n"
        f"        grid-template-columns: 1fr auto;\n"
        f"        grid-template-rows: auto auto;\n"
        f"        gap: 0.35rem 0.75rem;\n"
        f"        padding: 0.85rem 1rem;\n"
        f"        border: 0;\n"
        f"        background: transparent;\n"
        f"        color: inherit;\n"
        f"        text-align: left;\n"
        f"        cursor: pointer;\n"
        f"        font: inherit;\n"
        f"    }}\n"
        f"    #{block_id} .quote-card__quote-text {{\n"
        f"        grid-column: 1; grid-row: 1;\n"
        f"        font-weight: 500;\n"
        f"        font-size: 14px;\n"
        f"    }}\n"
        f"    #{block_id} .quote-card__toggle {{\n"
        f"        grid-column: 2; grid-row: 1 / 3;\n"
        f"        align-self: center;\n"
        f"        color: var(--color-text-secondary);\n"
        f"        font-size: 0.85rem;\n"
        f"        user-select: none;\n"
        f"    }}\n"
        f"    #{block_id} .quote-card__meta {{\n"
        f"        grid-column: 1; grid-row: 2;\n"
        f"        display: flex;\n"
        f"        flex-wrap: wrap;\n"
        f"        gap: 0.45rem;\n"
        f"        align-items: center;\n"
        f"        color: var(--color-text-secondary);\n"
        f"        font-size: 12px;\n"
        f"    }}\n"
        f"    #{block_id} .confidence-badge {{\n"
        f"        border: 1px solid var(--color-border-primary);\n"
        f"        border-radius: 999px;\n"
        f"        padding: 0.1rem 0.45rem;\n"
        f"        background: var(--color-background-secondary);\n"
        f"        color: var(--color-text-primary);\n"
        f"    }}\n"
        f"    #{block_id} .quote-card__full {{\n"
        f"        padding: 0 1rem 1rem;\n"
        f"    }}\n"
        f"    #{block_id} .quote-card__full-text {{\n"
        f"        font-style: italic;\n"
        f"        font-size: 13px;\n"
        f"        color: var(--color-text-secondary);\n"
        f"        border-top: 0.5px solid var(--color-border-primary);\n"
        f"        padding-top: 0.75rem;\n"
        f"        margin-top: 0;\n"
        f"    }}\n"
        f"    #{block_id} .quote-card__ref,\n"
        f"    #{block_id} .quote-empty {{\n"
        f"        color: var(--color-text-secondary);\n"
        f"        font-size: 0.86rem;\n"
        f"    }}\n"
        f"</style>\n"
        f'<div class="pattern-interactive__header">'
        f'<h3>{html.escape(pid_pattern)} / {html.escape(active_meta["name"])}</h3>'
        f'<div class="pattern-interactive__meta">'
        f'{_occ_label} participants / confidence {_confidence}'
        f'</div>'
        f'</div>\n'
        f'<div class="pattern-interactive__intro">'
        f'{interpretation_prose}'
        f'</div>\n'
        f'<div class="tier-grid" aria-label="Confidence tier overview">'
        f'{"".join(tier_cards)}'
        f'</div>\n'
        f'<div class="quote-explorer" aria-label="Quote explorer">'
        f'{"".join(quote_cards)}'
        f'</div>\n'
        f"<script>\n"
        f"(function() {{\n"
        f'    const root = document.getElementById("{block_id}");\n'
        f"    if (!root) return;\n"
        f'    const quoteCards = Array.from(root.querySelectorAll(".quote-card"));\n'
        f'    const pidRefs = Array.from(root.querySelectorAll(".pid-ref"));\n'
        f"    quoteCards.forEach((card) => {{\n"
        f'        const button = card.querySelector(".quote-card__summary");\n'
        f'        const full = card.querySelector(".quote-card__full");\n'
        f"        if (!button || !full) return;\n"
        f"        button.addEventListener('click', () => {{\n"
        f'            const expanded = button.getAttribute("aria-expanded") === "true";\n'
        f'            button.setAttribute("aria-expanded", String(!expanded));\n'
        f"            full.hidden = expanded;\n"
        f'            const toggle = button.querySelector(".quote-card__toggle");\n'
        f'            if (toggle) toggle.textContent = expanded ? "\u2193" : "\u2191";\n'
        f"        }});\n"
        f"    }});\n"
        f"    function clearHighlight() {{\n"
        f"        quoteCards.forEach((card) => {{\n"
        f'            card.classList.remove("is-highlighted", "is-muted");\n'
        f'            if (card.dataset.autoExpanded === "true") {{\n'
        f'                const btn = card.querySelector(".quote-card__summary");\n'
        f'                const full = card.querySelector(".quote-card__full");\n'
        f'                const toggle = btn && btn.querySelector(".quote-card__toggle");\n'
        f'                if (btn) btn.setAttribute("aria-expanded", "false");\n'
        f"                if (full) full.hidden = true;\n"
        f'                if (toggle) toggle.textContent = "\u2193";\n'
        f"                delete card.dataset.autoExpanded;\n"
        f"            }}\n"
        f"        }});\n"
        f'        pidRefs.forEach((ref) => ref.classList.remove("is-active"));\n'
        f"    }}\n"
        f"    pidRefs.forEach((ref) => {{\n"
        f"        ref.addEventListener('click', () => {{\n"
        f'            const pids = (ref.dataset.pids || "")\n'
        f'                .split(",")\n'
        f'                .map((pid) => pid.trim())\n'
        f"                .filter(Boolean);\n"
        f'            const isActive = ref.classList.contains("is-active");\n'
        f"            clearHighlight();\n"
        f"            if (isActive || pids.length === 0) return;\n"
        f'            ref.classList.add("is-active");\n'
        f"            quoteCards.forEach((card) => {{\n"
        f"                if (pids.includes(card.dataset.pid)) {{\n"
        f'                    card.classList.add("is-highlighted");\n'
        f'                    const btn = card.querySelector(".quote-card__summary");\n'
        f'                    const full = card.querySelector(".quote-card__full");\n'
        f'                    const toggle = btn && btn.querySelector(".quote-card__toggle");\n'
        f'                    if (btn && btn.getAttribute("aria-expanded") !== "true") {{\n'
        f'                        btn.setAttribute("aria-expanded", "true");\n'
        f"                        if (full) full.hidden = false;\n"
        f'                        if (toggle) toggle.textContent = "\u2191";\n'
        f'                        card.dataset.autoExpanded = "true";\n'
        f"                    }}\n"
        f"                }} else {{\n"
        f'                    card.classList.add("is-muted");\n'
        f"                }}\n"
        f"            }});\n"
        f"        }});\n"
        f"    }});\n"
        f"}})();\n"
        f"</script>\n"
        f"</section>\n"
    )


def render_p1_dotplot_interactive(quotes_df, participants_df):
    """P1 Layer 2: interactive dot plot (60%) + quote panel (40%). Self-contained HTML."""
    GROUP_MAP = {
        "P02": "Lịch trình quá nặng / thụ động",
        "P03": "Lịch trình quá nặng / thụ động",
        "P04": "Lịch trình quá nặng / thụ động",
        "P11": "Lịch trình quá nặng / thụ động",
        "P01": "Cần chất lượng truyền tải",
        "P08": "Cần chất lượng truyền tải",
        "P10": "Cần chất lượng truyền tải",
        "P05": "Muốn chủ động hơn / góc ngành",
        "P06": "Muốn chủ động hơn / góc ngành",
        "P07": "Muốn chủ động hơn / góc ngành",
        "P13": "Muốn chủ động hơn / góc ngành",
    }
    GROUP_COLORS = {
        "Lịch trình quá nặng / thụ động": {"main": "#B5593D", "dark": "#8B3D22"},
        "Cần chất lượng truyền tải":      {"main": "#2A7A5B", "dark": "#1A5A42"},
        "Muốn chủ động hơn / góc ngành":  {"main": "#5B4B9E", "dark": "#3E337A"},
    }
    GROUP_ORDER = [
        "Lịch trình quá nặng / thụ động",
        "Cần chất lượng truyền tải",
        "Muốn chủ động hơn / góc ngành",
    ]
    LENS_SHAPE = {"customer": "circle", "industry": "square", "lead_user": "diamond"}
    block_id = "p1-dotplot"

    p1_q = (
        quotes_df[quotes_df["pattern_id"] == "P1"]
        .merge(participants_df[["pid", "lens"]], on="pid", how="left")
        .sort_values("pid")
    )

    rows_js = []
    seen_pid = set()
    for _, r in p1_q.iterrows():
        pid = str(r["pid"])
        if pid in seen_pid:
            continue
        seen_pid.add(pid)
        rows_js.append({
            "pid": pid,
            "lens": str(r["lens"]) if pd.notna(r.get("lens")) else "",
            "confidence": str(r["confidence_level"]) if pd.notna(r.get("confidence_level")) else "",
            "short": str(r["quote_short"]) if pd.notna(r.get("quote_short")) else "",
            "full": str(r["quote_full"]) if pd.notna(r.get("quote_full")) else "",
            "ref": str(r["ref_id"]) if pd.notna(r.get("ref_id")) else "",
        })
    quotes_json = json.dumps(rows_js, ensure_ascii=False).replace("</", "<\\/")
    p1_pids_json = json.dumps(list(GROUP_MAP.keys()))

    group_pids = {g: [] for g in GROUP_ORDER}
    placed_pids = set()
    for _, r in p1_q.iterrows():
        pid = str(r["pid"])
        if pid in placed_pids:
            continue
        lens = str(r["lens"]) if pd.notna(r.get("lens")) else "customer"
        if pid in GROUP_MAP:
            group_pids[GROUP_MAP[pid]].append((pid, lens))
            placed_pids.add(pid)

    dot_rows_html = ""
    for g in GROUP_ORDER:
        colors = GROUP_COLORS[g]
        dots_html = ""
        for pid, lens in group_pids[g]:
            shape = LENS_SHAPE.get(lens, "circle")
            dots_html += (
                f'<button class="p1-dot p1-dot--{shape}" data-pid="{pid}"'
                f' style="--dot-main:{colors["main"]};--dot-dark:{colors["dark"]}"'
                f' aria-label="{pid}" type="button">'
                f'<span class="p1-dot-shape"></span>'
                f'<span class="p1-dot-label">{pid}</span>'
                f'</button>'
            )
        dot_rows_html += (
            f'<div class="p1-group-row">'
            f'<span class="p1-group-label">{html.escape(g)}</span>'
            f'<div class="p1-dots">{dots_html}</div>'
            f'</div>'
        )

    legend_html = (
        '<div class="p1-legend">'
        '<span class="p1-legend-item">'
        '<span class="p1-leg p1-leg--circle"></span>customer</span>'
        '<span class="p1-legend-item">'
        '<span class="p1-leg p1-leg--square"></span>industry</span>'
        '<span class="p1-legend-item">'
        '<span class="p1-leg p1-leg--diamond"></span>lead user</span>'
        '</div>'
    )

    css = (
        f"#{block_id} "
        "{display:grid;grid-template-columns:3fr 2fr;gap:1.5rem;align-items:start;margin:1.5rem 0;}"
        ".p1-plot-side{padding:0.25rem 0;}"
        ".p1-group-row{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.9rem;}"
        ".p1-group-label{min-width:11rem;font-size:0.875rem;color:var(--ink,#2c2c2c);line-height:1.3;}"
        ".p1-dots{display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap;}"
        ".p1-dot{background:none;border:none;padding:0.2rem 0.15rem;cursor:pointer;"
        "display:flex;flex-direction:column;align-items:center;gap:0.18rem;outline:none;}"
        ".p1-dot-shape{width:20px;height:20px;background:var(--dot-main);"
        "display:block;transition:filter 0.15s;}"
        ".p1-dot--circle .p1-dot-shape{border-radius:50%;}"
        ".p1-dot--square .p1-dot-shape{border-radius:2px;}"
        ".p1-dot--diamond .p1-dot-shape{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".p1-dot:hover .p1-dot-shape,.p1-dot.is-active .p1-dot-shape{"
        "filter:drop-shadow(0 0 5px var(--dot-dark)) brightness(1.12);}"
        ".p1-dot-label{font-size:0.72rem;color:var(--muted,#888);line-height:1;}"
        ".p1-dot.is-active .p1-dot-label{color:var(--ink,#2c2c2c);font-weight:600;}"
        ".p1-legend{display:flex;gap:1rem;margin-top:0.6rem;padding-top:0.5rem;"
        "border-top:1px solid var(--line,#d0ccc8);}"
        ".p1-legend-item{display:flex;align-items:center;gap:0.35rem;"
        "font-size:0.78rem;color:var(--muted,#888);}"
        ".p1-leg{width:11px;height:11px;background:var(--muted,#888);display:inline-block;}"
        ".p1-leg--circle{border-radius:50%;}"
        ".p1-leg--square{border-radius:2px;}"
        ".p1-leg--diamond{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".p1-quote-side{min-height:7rem;}"
        ".p1-hint{font-size:0.875rem;color:var(--muted,#888);font-style:italic;margin:0.5rem 0 0;}"
        ".p1-quote-panel{background:var(--bg-soft,#f7f7f5);border-radius:0.7rem;padding:1rem 1.1rem;}"
        ".p1-qpid{font-size:0.78rem;font-weight:600;color:var(--muted,#888);"
        "margin:0 0 0.4rem;text-transform:uppercase;letter-spacing:0.03em;}"
        ".p1-qshort{font-size:0.9rem;font-weight:500;color:var(--ink,#2c2c2c);margin:0;font-style:italic;}"
        ".p1-qfull{font-size:0.82rem;color:var(--muted,#888);margin:0.5rem 0 0.3rem;"
        "border-top:1px solid var(--line,#d0ccc8);padding-top:0.5rem;}"
        ".p1-qref{font-size:0.73rem;color:var(--muted,#888);margin:0.2rem 0 0;"
        "font-family:monospace;opacity:0.75;}"
    )

    js = (
        "(function(){"
        f"var QUOTES={quotes_json};"
        f"var P1PIDS=new Set({p1_pids_json});"
        f"var block=document.getElementById('{block_id}');"
        "if(!block)return;"
        f"var quoteDiv=document.getElementById('{block_id}-quote');"
        "var hint=block.querySelector('.p1-hint');"
        "var activeBtn=null;"
        "var QMAP={};"
        "QUOTES.forEach(function(q){QMAP[q.pid]=q;});"
        "function showQuote(btn){"
        "if(activeBtn)activeBtn.classList.remove('is-active');"
        "activeBtn=btn;"
        "btn.classList.add('is-active');"
        "var pid=btn.dataset.pid;"
        "var q=QMAP[pid];"
        "if(!q)return;"
        "quoteDiv.querySelector('.p1-qpid').textContent=pid+' \u00b7 '+q.lens;"
        "quoteDiv.querySelector('.p1-qshort').textContent='\u201c'+q.short+'\u201d';"
        "var fullEl=quoteDiv.querySelector('.p1-qfull');"
        "if(q.full&&q.full!==q.short){fullEl.textContent=q.full;fullEl.style.display='block';}"
        "else{fullEl.style.display='none';}"
        "quoteDiv.querySelector('.p1-qref').textContent=q.ref||'';"
        "quoteDiv.style.display='block';"
        "if(hint)hint.style.display='none';"
        "}"
        "block.querySelectorAll('.p1-dot').forEach(function(btn){"
        "btn.addEventListener('click',function(){"
        "if(activeBtn===btn)return;"
        "showQuote(btn);"
        "});"
        "});"
        "document.querySelectorAll('.pid-ref').forEach(function(span){"
        "var pids=(span.dataset.pids||'').split(',').map(function(s){return s.trim();});"
        "var relevant=pids.filter(function(p){return P1PIDS.has(p);});"
        "if(!relevant.length)return;"
        "span.addEventListener('click',function(){"
        "var first=relevant[0];"
        "var dot=block.querySelector('.p1-dot[data-pid=\"'+first+'\"]');"
        "if(dot)showQuote(dot);"
        "});"
        "});"
        "})();"
    )

    return (
        f'<section id="{block_id}" class="p1-dotplot-block">\n'
        f'<style>\n{css}\n</style>\n'
        f'<div class="p1-plot-side">\n{dot_rows_html}\n{legend_html}\n</div>\n'
        f'<div class="p1-quote-side">\n'
        f'<div id="{block_id}-quote" class="p1-quote-panel" style="display:none">'
        f'<p class="p1-qpid"></p>'
        f'<p class="p1-qshort"></p>'
        f'<p class="p1-qfull"></p>'
        f'<p class="p1-qref"></p>'
        f'</div>\n'
        f'<p class="p1-hint">Ch\u1ecdn m\u1ed9t participant \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
        f'</div>\n'
        f'<script>\n{js}\n</script>\n'
        f'</section>\n'
    )


def render_p2_dotplot_interactive(quotes_df, participants_df):
    """P2 Layer 2: interactive dot plot (60%) + quote panel (40%). Self-contained HTML."""
    GROUP_MAP = {
        "P05": "Người đồng hành là điều kiện",
        "P11": "Người đồng hành là điều kiện",
        "P04": "Bị động / gia đình là ưu tiên",
        "P10": "Bị động / gia đình là ưu tiên",
        "P06": "Ngữ cảnh tín ngưỡng",
    }
    GROUP_COLORS = {
        "Người đồng hành là điều kiện": {"main": "#378ADD", "dark": "#185FA5"},
        "Bị động / gia đình là ưu tiên": {"main": "#7F77DD", "dark": "#534AB7"},
        "Ngữ cảnh tín ngưỡng":          {"main": "#D4537E", "dark": "#993556"},
    }
    GROUP_ORDER = [
        "Người đồng hành là điều kiện",
        "Bị động / gia đình là ưu tiên",
        "Ngữ cảnh tín ngưỡng",
    ]
    LENS_SHAPE = {"customer": "circle", "industry": "square", "lead_user": "diamond"}
    block_id = "p2-dotplot"

    p2_q = (
        quotes_df[quotes_df["pattern_id"] == "P2"]
        .merge(participants_df[["pid", "lens"]], on="pid", how="left")
        .sort_values("pid")
    )

    rows_js = []
    for _, r in p2_q.iterrows():
        rows_js.append({
            "pid": str(r["pid"]),
            "lens": str(r["lens"]) if pd.notna(r.get("lens")) else "",
            "confidence": str(r["confidence_level"]) if pd.notna(r.get("confidence_level")) else "",
            "short": str(r["quote_short"]) if pd.notna(r.get("quote_short")) else "",
            "full": str(r["quote_full"]) if pd.notna(r.get("quote_full")) else "",
            "ref": str(r["ref_id"]) if pd.notna(r.get("ref_id")) else "",
        })
    quotes_json = json.dumps(rows_js, ensure_ascii=False).replace("</", "<\\/")
    p2_pids_json = json.dumps(list(GROUP_MAP.keys()))

    group_pids = {g: [] for g in GROUP_ORDER}
    for _, r in p2_q.iterrows():
        pid = str(r["pid"])
        lens = str(r["lens"]) if pd.notna(r.get("lens")) else "customer"
        if pid in GROUP_MAP:
            group_pids[GROUP_MAP[pid]].append((pid, lens))

    dot_rows_html = ""
    for g in GROUP_ORDER:
        colors = GROUP_COLORS[g]
        dots_html = ""
        for pid, lens in group_pids[g]:
            shape = LENS_SHAPE.get(lens, "circle")
            dots_html += (
                f'<button class="p2-dot p2-dot--{shape}" data-pid="{pid}"'
                f' style="--dot-main:{colors["main"]};--dot-dark:{colors["dark"]}"'
                f' aria-label="{pid}" type="button">'
                f'<span class="p2-dot-shape"></span>'
                f'<span class="p2-dot-label">{pid}</span>'
                f'</button>'
            )
        dot_rows_html += (
            f'<div class="p2-group-row">'
            f'<span class="p2-group-label">{html.escape(g)}</span>'
            f'<div class="p2-dots">{dots_html}</div>'
            f'</div>'
        )

    legend_html = (
        '<div class="p2-legend">'
        '<span class="p2-legend-item">'
        '<span class="p2-leg p2-leg--circle"></span>customer</span>'
        '<span class="p2-legend-item">'
        '<span class="p2-leg p2-leg--square"></span>industry</span>'
        '<span class="p2-legend-item">'
        '<span class="p2-leg p2-leg--diamond"></span>lead user</span>'
        '</div>'
    )

    css = (
        f"#{block_id} "
        "{display:grid;grid-template-columns:3fr 2fr;gap:1.5rem;align-items:start;margin:1.5rem 0;}"
        ".p2-plot-side{padding:0.25rem 0;}"
        ".p2-group-row{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.9rem;}"
        ".p2-group-label{min-width:11rem;font-size:0.875rem;color:var(--ink,#2c2c2c);line-height:1.3;}"
        ".p2-dots{display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap;}"
        ".p2-dot{background:none;border:none;padding:0.2rem 0.15rem;cursor:pointer;"
        "display:flex;flex-direction:column;align-items:center;gap:0.18rem;outline:none;}"
        ".p2-dot-shape{width:20px;height:20px;background:var(--dot-main);"
        "display:block;transition:filter 0.15s;}"
        ".p2-dot--circle .p2-dot-shape{border-radius:50%;}"
        ".p2-dot--square .p2-dot-shape{border-radius:2px;}"
        ".p2-dot--diamond .p2-dot-shape{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".p2-dot:hover .p2-dot-shape,.p2-dot.is-active .p2-dot-shape{"
        "filter:drop-shadow(0 0 5px var(--dot-dark)) brightness(1.12);}"
        ".p2-dot-label{font-size:0.72rem;color:var(--muted,#888);line-height:1;}"
        ".p2-dot.is-active .p2-dot-label{color:var(--ink,#2c2c2c);font-weight:600;}"
        ".p2-legend{display:flex;gap:1rem;margin-top:0.6rem;padding-top:0.5rem;"
        "border-top:1px solid var(--line,#d0ccc8);}"
        ".p2-legend-item{display:flex;align-items:center;gap:0.35rem;"
        "font-size:0.78rem;color:var(--muted,#888);}"
        ".p2-leg{width:11px;height:11px;background:var(--muted,#888);display:inline-block;}"
        ".p2-leg--circle{border-radius:50%;}"
        ".p2-leg--square{border-radius:2px;}"
        ".p2-leg--diamond{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".p2-quote-side{min-height:7rem;}"
        ".p2-hint{font-size:0.875rem;color:var(--muted,#888);font-style:italic;margin:0.5rem 0 0;}"
        ".p2-quote-panel{background:var(--bg-soft,#f7f7f5);border-radius:0.7rem;padding:1rem 1.1rem;}"
        ".p2-qpid{font-size:0.78rem;font-weight:600;color:var(--muted,#888);"
        "margin:0 0 0.4rem;text-transform:uppercase;letter-spacing:0.03em;}"
        ".p2-qshort{font-size:0.9rem;font-weight:500;color:var(--ink,#2c2c2c);margin:0;font-style:italic;}"
        ".p2-qfull{font-size:0.82rem;color:var(--muted,#888);margin:0.5rem 0 0.3rem;"
        "border-top:1px solid var(--line,#d0ccc8);padding-top:0.5rem;}"
        ".p2-qref{font-size:0.73rem;color:var(--muted,#888);margin:0.2rem 0 0;"
        "font-family:monospace;opacity:0.75;}"
    )

    js = (
        "(function(){"
        f"var QUOTES={quotes_json};"
        f"var P2PIDS=new Set({p2_pids_json});"
        f"var block=document.getElementById('{block_id}');"
        "if(!block)return;"
        f"var quoteDiv=document.getElementById('{block_id}-quote');"
        "var hint=block.querySelector('.p2-hint');"
        "var activeBtn=null;"
        "var QMAP={};"
        "QUOTES.forEach(function(q){QMAP[q.pid]=q;});"
        "function showQuote(btn){"
        "if(activeBtn)activeBtn.classList.remove('is-active');"
        "activeBtn=btn;"
        "btn.classList.add('is-active');"
        "var pid=btn.dataset.pid;"
        "var q=QMAP[pid];"
        "if(!q)return;"
        "quoteDiv.querySelector('.p2-qpid').textContent=pid+' \u00b7 '+q.lens;"
        "quoteDiv.querySelector('.p2-qshort').textContent='\u201c'+q.short+'\u201d';"
        "var fullEl=quoteDiv.querySelector('.p2-qfull');"
        "if(q.full&&q.full!==q.short){fullEl.textContent=q.full;fullEl.style.display='block';}"
        "else{fullEl.style.display='none';}"
        "quoteDiv.querySelector('.p2-qref').textContent=q.ref||'';"
        "quoteDiv.style.display='block';"
        "if(hint)hint.style.display='none';"
        "}"
        "block.querySelectorAll('.p2-dot').forEach(function(btn){"
        "btn.addEventListener('click',function(){"
        "if(activeBtn===btn)return;"
        "showQuote(btn);"
        "});"
        "});"
        "document.querySelectorAll('.pid-ref').forEach(function(span){"
        "var pids=(span.dataset.pids||'').split(',').map(function(s){return s.trim();});"
        "var relevant=pids.filter(function(p){return P2PIDS.has(p);});"
        "if(!relevant.length)return;"
        "span.addEventListener('click',function(){"
        "var first=relevant[0];"
        "var dot=block.querySelector('.p2-dot[data-pid=\"'+first+'\"]');"
        "if(dot)showQuote(dot);"
        "});"
        "});"
        "})();"
    )

    return (
        f'<section id="{block_id}" class="p2-dotplot-block">\n'
        f'<style>\n{css}\n</style>\n'
        f'<div class="p2-plot-side">\n{dot_rows_html}\n{legend_html}\n</div>\n'
        f'<div class="p2-quote-side">\n'
        f'<div id="{block_id}-quote" class="p2-quote-panel" style="display:none">'
        f'<p class="p2-qpid"></p>'
        f'<p class="p2-qshort"></p>'
        f'<p class="p2-qfull"></p>'
        f'<p class="p2-qref"></p>'
        f'</div>\n'
        f'<p class="p2-hint">Ch\u1ecdn m\u1ed9t participant \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
        f'</div>\n'
        f'<script>\n{js}\n</script>\n'
        f'</section>\n'
    )


def render_p3_dotplot_interactive(quotes_df, participants_df):
    """P3 Layer 2: interactive dot plot (60%) + quote panel (40%). Self-contained HTML."""
    GROUP_MAP = {
        "P05": "Tự nhận phù hợp",
        "P08": "Tự nhận phù hợp",
        "P10": "Tự nhận phù hợp",
        "P14": "Tự nhận phù hợp",
        "P02": "Tự loại",
        "P04": "Tự loại",
        "P06": "Tự loại",
        "P01": "Phê phán định vị",
        "P03": "Phê phán định vị",
        "P07": "Phê phán định vị",
    }
    GROUP_COLORS = {
        "Tự nhận phù hợp":  {"main": "#4E9B8F", "dark": "#2E7A6F"},
        "Tự loại":          {"main": "#B56B6B", "dark": "#8B4444"},
        "Phê phán định vị": {"main": "#7A8D9E", "dark": "#5A6D7E"},
    }
    GROUP_ORDER = [
        "Tự nhận phù hợp",
        "Tự loại",
        "Phê phán định vị",
    ]
    LENS_SHAPE = {"customer": "circle", "industry": "square", "lead_user": "diamond"}
    block_id = "p3-dotplot"

    p3_q = (
        quotes_df[quotes_df["pattern_id"] == "P3"]
        .merge(participants_df[["pid", "lens"]], on="pid", how="left")
        .sort_values("pid")
    )

    rows_js = []
    seen_pid = set()
    for _, r in p3_q.iterrows():
        pid = str(r["pid"])
        if pid in seen_pid:
            continue
        seen_pid.add(pid)
        rows_js.append({
            "pid": pid,
            "lens": str(r["lens"]) if pd.notna(r.get("lens")) else "",
            "confidence": str(r["confidence_level"]) if pd.notna(r.get("confidence_level")) else "",
            "short": str(r["quote_short"]) if pd.notna(r.get("quote_short")) else "",
            "full": str(r["quote_full"]) if pd.notna(r.get("quote_full")) else "",
            "ref": str(r["ref_id"]) if pd.notna(r.get("ref_id")) else "",
        })
    quotes_json = json.dumps(rows_js, ensure_ascii=False).replace("</", "<\\/")
    p3_pids_json = json.dumps(list(GROUP_MAP.keys()))

    group_pids = {g: [] for g in GROUP_ORDER}
    placed_pids = set()
    for _, r in p3_q.iterrows():
        pid = str(r["pid"])
        if pid in placed_pids:
            continue
        lens = str(r["lens"]) if pd.notna(r.get("lens")) else "customer"
        if pid in GROUP_MAP:
            group_pids[GROUP_MAP[pid]].append((pid, lens))
            placed_pids.add(pid)

    dot_rows_html = ""
    for g in GROUP_ORDER:
        colors = GROUP_COLORS[g]
        dots_html = ""
        for pid, lens in group_pids[g]:
            shape = LENS_SHAPE.get(lens, "circle")
            dots_html += (
                f'<button class="p3-dot p3-dot--{shape}" data-pid="{pid}"'
                f' style="--dot-main:{colors["main"]};--dot-dark:{colors["dark"]}"'
                f' aria-label="{pid}" type="button">'
                f'<span class="p3-dot-shape"></span>'
                f'<span class="p3-dot-label">{pid}</span>'
                f'</button>'
            )
        dot_rows_html += (
            f'<div class="p3-group-row">'
            f'<span class="p3-group-label">{html.escape(g)}</span>'
            f'<div class="p3-dots">{dots_html}</div>'
            f'</div>'
        )

    legend_html = (
        '<div class="p3-legend">'
        '<span class="p3-legend-item">'
        '<span class="p3-leg p3-leg--circle"></span>customer</span>'
        '<span class="p3-legend-item">'
        '<span class="p3-leg p3-leg--square"></span>industry</span>'
        '<span class="p3-legend-item">'
        '<span class="p3-leg p3-leg--diamond"></span>lead user</span>'
        '</div>'
    )

    css = (
        f"#{block_id} "
        "{display:grid;grid-template-columns:3fr 2fr;gap:1.5rem;align-items:start;margin:1.5rem 0;}"
        ".p3-plot-side{padding:0.25rem 0;}"
        ".p3-group-row{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.9rem;}"
        ".p3-group-label{min-width:11rem;font-size:0.875rem;color:var(--ink,#2c2c2c);line-height:1.3;}"
        ".p3-dots{display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap;}"
        ".p3-dot{background:none;border:none;padding:0.2rem 0.15rem;cursor:pointer;"
        "display:flex;flex-direction:column;align-items:center;gap:0.18rem;outline:none;}"
        ".p3-dot-shape{width:20px;height:20px;background:var(--dot-main);"
        "display:block;transition:filter 0.15s;}"
        ".p3-dot--circle .p3-dot-shape{border-radius:50%;}"
        ".p3-dot--square .p3-dot-shape{border-radius:2px;}"
        ".p3-dot--diamond .p3-dot-shape{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".p3-dot:hover .p3-dot-shape,.p3-dot.is-active .p3-dot-shape{"
        "filter:drop-shadow(0 0 5px var(--dot-dark)) brightness(1.12);}"
        ".p3-dot-label{font-size:0.72rem;color:var(--muted,#888);line-height:1;}"
        ".p3-dot.is-active .p3-dot-label{color:var(--ink,#2c2c2c);font-weight:600;}"
        ".p3-legend{display:flex;gap:1rem;margin-top:0.6rem;padding-top:0.5rem;"
        "border-top:1px solid var(--line,#d0ccc8);}"
        ".p3-legend-item{display:flex;align-items:center;gap:0.35rem;"
        "font-size:0.78rem;color:var(--muted,#888);}"
        ".p3-leg{width:11px;height:11px;background:var(--muted,#888);display:inline-block;}"
        ".p3-leg--circle{border-radius:50%;}"
        ".p3-leg--square{border-radius:2px;}"
        ".p3-leg--diamond{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".p3-quote-side{min-height:7rem;}"
        ".p3-hint{font-size:0.875rem;color:var(--muted,#888);font-style:italic;margin:0.5rem 0 0;}"
        ".p3-quote-panel{background:var(--bg-soft,#f7f7f5);border-radius:0.7rem;padding:1rem 1.1rem;}"
        ".p3-qpid{font-size:0.78rem;font-weight:600;color:var(--muted,#888);"
        "margin:0 0 0.4rem;text-transform:uppercase;letter-spacing:0.03em;}"
        ".p3-qshort{font-size:0.9rem;font-weight:500;color:var(--ink,#2c2c2c);margin:0;font-style:italic;}"
        ".p3-qfull{font-size:0.82rem;color:var(--muted,#888);margin:0.5rem 0 0.3rem;"
        "border-top:1px solid var(--line,#d0ccc8);padding-top:0.5rem;}"
        ".p3-qref{font-size:0.73rem;color:var(--muted,#888);margin:0.2rem 0 0;"
        "font-family:monospace;opacity:0.75;}"
    )

    js = (
        "(function(){"
        f"var QUOTES={quotes_json};"
        f"var P3PIDS=new Set({p3_pids_json});"
        f"var block=document.getElementById('{block_id}');"
        "if(!block)return;"
        f"var quoteDiv=document.getElementById('{block_id}-quote');"
        "var hint=block.querySelector('.p3-hint');"
        "var activeBtn=null;"
        "var QMAP={};"
        "QUOTES.forEach(function(q){QMAP[q.pid]=q;});"
        "function showQuote(btn){"
        "if(activeBtn)activeBtn.classList.remove('is-active');"
        "activeBtn=btn;"
        "btn.classList.add('is-active');"
        "var pid=btn.dataset.pid;"
        "var q=QMAP[pid];"
        "if(!q)return;"
        "quoteDiv.querySelector('.p3-qpid').textContent=pid+' \u00b7 '+q.lens;"
        "quoteDiv.querySelector('.p3-qshort').textContent='\u201c'+q.short+'\u201d';"
        "var fullEl=quoteDiv.querySelector('.p3-qfull');"
        "if(q.full&&q.full!==q.short){fullEl.textContent=q.full;fullEl.style.display='block';}"
        "else{fullEl.style.display='none';}"
        "quoteDiv.querySelector('.p3-qref').textContent=q.ref||'';"
        "quoteDiv.style.display='block';"
        "if(hint)hint.style.display='none';"
        "}"
        "block.querySelectorAll('.p3-dot').forEach(function(btn){"
        "btn.addEventListener('click',function(){"
        "if(activeBtn===btn)return;"
        "showQuote(btn);"
        "});"
        "});"
        "document.querySelectorAll('.pid-ref').forEach(function(span){"
        "var pids=(span.dataset.pids||'').split(',').map(function(s){return s.trim();});"
        "var relevant=pids.filter(function(p){return P3PIDS.has(p);});"
        "if(!relevant.length)return;"
        "span.addEventListener('click',function(){"
        "var first=relevant[0];"
        "var dot=block.querySelector('.p3-dot[data-pid=\"'+first+'\"]');"
        "if(dot)showQuote(dot);"
        "});"
        "});"
        "})();"
    )

    return (
        f'<section id="{block_id}" class="p3-dotplot-block">\n'
        f'<style>\n{css}\n</style>\n'
        f'<div class="p3-plot-side">\n{dot_rows_html}\n{legend_html}\n</div>\n'
        f'<div class="p3-quote-side">\n'
        f'<div id="{block_id}-quote" class="p3-quote-panel" style="display:none">'
        f'<p class="p3-qpid"></p>'
        f'<p class="p3-qshort"></p>'
        f'<p class="p3-qfull"></p>'
        f'<p class="p3-qref"></p>'
        f'</div>\n'
        f'<p class="p3-hint">Ch\u1ecdn m\u1ed9t participant \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
        f'</div>\n'
        f'<script>\n{js}\n</script>\n'
        f'</section>\n'
    )


def render_h1_dotplot_interactive(quotes_df, participants_df):
    """H1 Layer 2: interactive dot plot (60%) + quote panel (40%). Self-contained HTML."""
    GROUP_MAP = {
        "P05": "Quan tâm và có trải nghiệm",
        "P11": "Quan tâm và có trải nghiệm",
        "P14": "Tò mò muốn khám phá",
        "P01": "Tâm linh theo hướng khác",
    }
    GROUP_COLORS = {
        "Quan tâm và có trải nghiệm": {"main": "#3D8B7A", "dark": "#2A6B5E"},
        "Tò mò muốn khám phá":        {"main": "#C4952A", "dark": "#8B6B1E"},
        "Tâm linh theo hướng khác":   {"main": "#8B6B9E", "dark": "#6B4B7E"},
    }
    GROUP_ORDER = [
        "Quan tâm và có trải nghiệm",
        "Tò mò muốn khám phá",
        "Tâm linh theo hướng khác",
    ]
    LENS_SHAPE = {"customer": "circle", "industry": "square", "lead_user": "diamond"}
    block_id = "h1-dotplot"

    h1_q = (
        quotes_df[quotes_df["pattern_id"] == "H1"]
        .merge(participants_df[["pid", "lens"]], on="pid", how="left")
        .sort_values("pid")
    )

    rows_js = []
    seen_pid = set()
    for _, r in h1_q.iterrows():
        pid = str(r["pid"])
        if pid in seen_pid:
            continue
        seen_pid.add(pid)
        rows_js.append({
            "pid": pid,
            "lens": str(r["lens"]) if pd.notna(r.get("lens")) else "",
            "confidence": str(r["confidence_level"]) if pd.notna(r.get("confidence_level")) else "",
            "short": str(r["quote_short"]) if pd.notna(r.get("quote_short")) else "",
            "full": str(r["quote_full"]) if pd.notna(r.get("quote_full")) else "",
            "ref": str(r["ref_id"]) if pd.notna(r.get("ref_id")) else "",
        })
    quotes_json = json.dumps(rows_js, ensure_ascii=False).replace("</", "<\\/")
    h1_pids_json = json.dumps(list(GROUP_MAP.keys()))

    group_pids = {g: [] for g in GROUP_ORDER}
    placed_pids = set()
    for _, r in h1_q.iterrows():
        pid = str(r["pid"])
        if pid in placed_pids:
            continue
        lens = str(r["lens"]) if pd.notna(r.get("lens")) else "customer"
        if pid in GROUP_MAP:
            group_pids[GROUP_MAP[pid]].append((pid, lens))
            placed_pids.add(pid)

    dot_rows_html = ""
    for g in GROUP_ORDER:
        colors = GROUP_COLORS[g]
        dots_html = ""
        for pid, lens in group_pids[g]:
            shape = LENS_SHAPE.get(lens, "circle")
            dots_html += (
                f'<button class="h1-dot h1-dot--{shape}" data-pid="{pid}"'
                f' style="--dot-main:{colors["main"]};--dot-dark:{colors["dark"]}"'
                f' aria-label="{pid}" type="button">'
                f'<span class="h1-dot-shape"></span>'
                f'<span class="h1-dot-label">{pid}</span>'
                f'</button>'
            )
        dot_rows_html += (
            f'<div class="h1-group-row">'
            f'<span class="h1-group-label">{html.escape(g)}</span>'
            f'<div class="h1-dots">{dots_html}</div>'
            f'</div>'
        )

    legend_html = (
        '<div class="h1-legend">'
        '<span class="h1-legend-item">'
        '<span class="h1-leg h1-leg--circle"></span>customer</span>'
        '<span class="h1-legend-item">'
        '<span class="h1-leg h1-leg--square"></span>industry</span>'
        '<span class="h1-legend-item">'
        '<span class="h1-leg h1-leg--diamond"></span>lead user</span>'
        '</div>'
    )

    css = (
        f"#{block_id} "
        "{display:grid;grid-template-columns:3fr 2fr;gap:1.5rem;align-items:start;margin:1.5rem 0;}"
        ".h1-plot-side{padding:0.25rem 0;}"
        ".h1-group-row{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.9rem;}"
        ".h1-group-label{min-width:11rem;font-size:0.875rem;color:var(--ink,#2c2c2c);line-height:1.3;}"
        ".h1-dots{display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap;}"
        ".h1-dot{background:none;border:none;padding:0.2rem 0.15rem;cursor:pointer;"
        "display:flex;flex-direction:column;align-items:center;gap:0.18rem;outline:none;}"
        ".h1-dot-shape{width:20px;height:20px;background:var(--dot-main);"
        "display:block;transition:filter 0.15s;}"
        ".h1-dot--circle .h1-dot-shape{border-radius:50%;}"
        ".h1-dot--square .h1-dot-shape{border-radius:2px;}"
        ".h1-dot--diamond .h1-dot-shape{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".h1-dot:hover .h1-dot-shape,.h1-dot.is-active .h1-dot-shape{"
        "filter:drop-shadow(0 0 5px var(--dot-dark)) brightness(1.12);}"
        ".h1-dot-label{font-size:0.72rem;color:var(--muted,#888);line-height:1;}"
        ".h1-dot.is-active .h1-dot-label{color:var(--ink,#2c2c2c);font-weight:600;}"
        ".h1-legend{display:flex;gap:1rem;margin-top:0.6rem;padding-top:0.5rem;"
        "border-top:1px solid var(--line,#d0ccc8);}"
        ".h1-legend-item{display:flex;align-items:center;gap:0.35rem;"
        "font-size:0.78rem;color:var(--muted,#888);}"
        ".h1-leg{width:11px;height:11px;background:var(--muted,#888);display:inline-block;}"
        ".h1-leg--circle{border-radius:50%;}"
        ".h1-leg--square{border-radius:2px;}"
        ".h1-leg--diamond{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".h1-quote-side{min-height:7rem;}"
        ".h1-hint{font-size:0.875rem;color:var(--muted,#888);font-style:italic;margin:0.5rem 0 0;}"
        ".h1-quote-panel{background:var(--bg-soft,#f7f7f5);border-radius:0.7rem;padding:1rem 1.1rem;}"
        ".h1-qpid{font-size:0.78rem;font-weight:600;color:var(--muted,#888);"
        "margin:0 0 0.4rem;text-transform:uppercase;letter-spacing:0.03em;}"
        ".h1-qshort{font-size:0.9rem;font-weight:500;color:var(--ink,#2c2c2c);margin:0;font-style:italic;}"
        ".h1-qfull{font-size:0.82rem;color:var(--muted,#888);margin:0.5rem 0 0.3rem;"
        "border-top:1px solid var(--line,#d0ccc8);padding-top:0.5rem;}"
        ".h1-qref{font-size:0.73rem;color:var(--muted,#888);margin:0.2rem 0 0;"
        "font-family:monospace;opacity:0.75;}"
    )

    js = (
        "(function(){"
        f"var QUOTES={quotes_json};"
        f"var H1PIDS=new Set({h1_pids_json});"
        f"var block=document.getElementById('{block_id}');"
        "if(!block)return;"
        f"var quoteDiv=document.getElementById('{block_id}-quote');"
        "var hint=block.querySelector('.h1-hint');"
        "var activeBtn=null;"
        "var QMAP={};"
        "QUOTES.forEach(function(q){QMAP[q.pid]=q;});"
        "function showQuote(btn){"
        "if(activeBtn)activeBtn.classList.remove('is-active');"
        "activeBtn=btn;"
        "btn.classList.add('is-active');"
        "var pid=btn.dataset.pid;"
        "var q=QMAP[pid];"
        "if(!q)return;"
        "quoteDiv.querySelector('.h1-qpid').textContent=pid+' \u00b7 '+q.lens;"
        "quoteDiv.querySelector('.h1-qshort').textContent='\u201c'+q.short+'\u201d';"
        "var fullEl=quoteDiv.querySelector('.h1-qfull');"
        "if(q.full&&q.full!==q.short){fullEl.textContent=q.full;fullEl.style.display='block';}"
        "else{fullEl.style.display='none';}"
        "quoteDiv.querySelector('.h1-qref').textContent=q.ref||'';"
        "quoteDiv.style.display='block';"
        "if(hint)hint.style.display='none';"
        "}"
        "block.querySelectorAll('.h1-dot').forEach(function(btn){"
        "btn.addEventListener('click',function(){"
        "if(activeBtn===btn)return;"
        "showQuote(btn);"
        "});"
        "});"
        "document.querySelectorAll('.pid-ref').forEach(function(span){"
        "var pids=(span.dataset.pids||'').split(',').map(function(s){return s.trim();});"
        "var relevant=pids.filter(function(p){return H1PIDS.has(p);});"
        "if(!relevant.length)return;"
        "span.addEventListener('click',function(){"
        "var first=relevant[0];"
        "var dot=block.querySelector('.h1-dot[data-pid=\"'+first+'\"]');"
        "if(dot)showQuote(dot);"
        "});"
        "});"
        "})();"
    )

    return (
        f'<section id="{block_id}" class="h1-dotplot-block">\n'
        f'<style>\n{css}\n</style>\n'
        f'<div class="h1-plot-side">\n{dot_rows_html}\n{legend_html}\n</div>\n'
        f'<div class="h1-quote-side">\n'
        f'<div id="{block_id}-quote" class="h1-quote-panel" style="display:none">'
        f'<p class="h1-qpid"></p>'
        f'<p class="h1-qshort"></p>'
        f'<p class="h1-qfull"></p>'
        f'<p class="h1-qref"></p>'
        f'</div>\n'
        f'<p class="h1-hint">Ch\u1ecdn m\u1ed9t participant \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
        f'</div>\n'
        f'<script>\n{js}\n</script>\n'
        f'</section>\n'
    )


def render_s1_dotplot_interactive(quotes_df, participants_df):
    """S1 Layer 2: interactive dot plot (60%) + quote panel (40%). Self-contained HTML."""
    GROUP_MAP = {
        "P03": "Quan sát ngành",
        "P07": "Quan sát ngành",
        "P09": "Phỏng đoán cá nhân",
        "P12": "Phỏng đoán cá nhân",
        "P11": "Kinh nghiệm thực tế",
    }
    GROUP_COLORS = {
        "Quan sát ngành":       {"main": "#6B7E9A", "dark": "#4A5E7A"},
        "Phỏng đoán cá nhân":   {"main": "#7A8E6B", "dark": "#5A6E4B"},
        "Kinh nghiệm thực tế": {"main": "#B8873A", "dark": "#8B6428"},
    }
    GROUP_ORDER = [
        "Quan sát ngành",
        "Phỏng đoán cá nhân",
        "Kinh nghiệm thực tế",
    ]
    LENS_SHAPE = {"customer": "circle", "industry": "square", "lead_user": "diamond"}
    block_id = "s1-dotplot"

    s1_q = (
        quotes_df[quotes_df["pattern_id"] == "S1"]
        .merge(participants_df[["pid", "lens"]], on="pid", how="left")
        .sort_values("pid")
    )

    rows_js = []
    seen_pid = set()
    for _, r in s1_q.iterrows():
        pid = str(r["pid"])
        if pid in seen_pid:
            continue
        seen_pid.add(pid)
        rows_js.append({
            "pid": pid,
            "lens": str(r["lens"]) if pd.notna(r.get("lens")) else "",
            "confidence": str(r["confidence_level"]) if pd.notna(r.get("confidence_level")) else "",
            "short": str(r["quote_short"]) if pd.notna(r.get("quote_short")) else "",
            "full": str(r["quote_full"]) if pd.notna(r.get("quote_full")) else "",
            "ref": str(r["ref_id"]) if pd.notna(r.get("ref_id")) else "",
        })
    quotes_json = json.dumps(rows_js, ensure_ascii=False).replace("</", "<\\/")
    s1_pids_json = json.dumps(list(GROUP_MAP.keys()))

    group_pids = {g: [] for g in GROUP_ORDER}
    placed_pids = set()
    for _, r in s1_q.iterrows():
        pid = str(r["pid"])
        if pid in placed_pids:
            continue
        lens = str(r["lens"]) if pd.notna(r.get("lens")) else "customer"
        if pid in GROUP_MAP:
            group_pids[GROUP_MAP[pid]].append((pid, lens))
            placed_pids.add(pid)

    dot_rows_html = ""
    for g in GROUP_ORDER:
        colors = GROUP_COLORS[g]
        dots_html = ""
        for pid, lens in group_pids[g]:
            shape = LENS_SHAPE.get(lens, "circle")
            dots_html += (
                f'<button class="s1-dot s1-dot--{shape}" data-pid="{pid}"'
                f' style="--dot-main:{colors["main"]};--dot-dark:{colors["dark"]}"'
                f' aria-label="{pid}" type="button">'
                f'<span class="s1-dot-shape"></span>'
                f'<span class="s1-dot-label">{pid}</span>'
                f'</button>'
            )
        dot_rows_html += (
            f'<div class="s1-group-row">'
            f'<span class="s1-group-label">{html.escape(g)}</span>'
            f'<div class="s1-dots">{dots_html}</div>'
            f'</div>'
        )

    legend_html = (
        '<div class="s1-legend">'
        '<span class="s1-legend-item">'
        '<span class="s1-leg s1-leg--circle"></span>customer</span>'
        '<span class="s1-legend-item">'
        '<span class="s1-leg s1-leg--square"></span>industry</span>'
        '<span class="s1-legend-item">'
        '<span class="s1-leg s1-leg--diamond"></span>lead user</span>'
        '</div>'
    )

    css = (
        f"#{block_id} "
        "{display:grid;grid-template-columns:3fr 2fr;gap:1.5rem;align-items:start;margin:1.5rem 0;}"
        ".s1-plot-side{padding:0.25rem 0;}"
        ".s1-group-row{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.9rem;}"
        ".s1-group-label{min-width:11rem;font-size:0.875rem;color:var(--ink,#2c2c2c);line-height:1.3;}"
        ".s1-dots{display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap;}"
        ".s1-dot{background:none;border:none;padding:0.2rem 0.15rem;cursor:pointer;"
        "display:flex;flex-direction:column;align-items:center;gap:0.18rem;outline:none;}"
        ".s1-dot-shape{width:20px;height:20px;background:var(--dot-main);"
        "display:block;transition:filter 0.15s;}"
        ".s1-dot--circle .s1-dot-shape{border-radius:50%;}"
        ".s1-dot--square .s1-dot-shape{border-radius:2px;}"
        ".s1-dot--diamond .s1-dot-shape{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".s1-dot:hover .s1-dot-shape,.s1-dot.is-active .s1-dot-shape{"
        "filter:drop-shadow(0 0 5px var(--dot-dark)) brightness(1.12);}"
        ".s1-dot-label{font-size:0.72rem;color:var(--muted,#888);line-height:1;}"
        ".s1-dot.is-active .s1-dot-label{color:var(--ink,#2c2c2c);font-weight:600;}"
        ".s1-legend{display:flex;gap:1rem;margin-top:0.6rem;padding-top:0.5rem;"
        "border-top:1px solid var(--line,#d0ccc8);}"
        ".s1-legend-item{display:flex;align-items:center;gap:0.35rem;"
        "font-size:0.78rem;color:var(--muted,#888);}"
        ".s1-leg{width:11px;height:11px;background:var(--muted,#888);display:inline-block;}"
        ".s1-leg--circle{border-radius:50%;}"
        ".s1-leg--square{border-radius:2px;}"
        ".s1-leg--diamond{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".s1-quote-side{min-height:7rem;}"
        ".s1-hint{font-size:0.875rem;color:var(--muted,#888);font-style:italic;margin:0.5rem 0 0;}"
        ".s1-quote-panel{background:var(--bg-soft,#f7f7f5);border-radius:0.7rem;padding:1rem 1.1rem;}"
        ".s1-qpid{font-size:0.78rem;font-weight:600;color:var(--muted,#888);"
        "margin:0 0 0.4rem;text-transform:uppercase;letter-spacing:0.03em;}"
        ".s1-qshort{font-size:0.9rem;font-weight:500;color:var(--ink,#2c2c2c);margin:0;font-style:italic;}"
        ".s1-qfull{font-size:0.82rem;color:var(--muted,#888);margin:0.5rem 0 0.3rem;"
        "border-top:1px solid var(--line,#d0ccc8);padding-top:0.5rem;}"
        ".s1-qref{font-size:0.73rem;color:var(--muted,#888);margin:0.2rem 0 0;"
        "font-family:monospace;opacity:0.75;}"
    )

    js = (
        "(function(){"
        f"var QUOTES={quotes_json};"
        f"var S1PIDS=new Set({s1_pids_json});"
        f"var block=document.getElementById('{block_id}');"
        "if(!block)return;"
        f"var quoteDiv=document.getElementById('{block_id}-quote');"
        "var hint=block.querySelector('.s1-hint');"
        "var activeBtn=null;"
        "var QMAP={};"
        "QUOTES.forEach(function(q){QMAP[q.pid]=q;});"
        "function showQuote(btn){"
        "if(activeBtn)activeBtn.classList.remove('is-active');"
        "activeBtn=btn;"
        "btn.classList.add('is-active');"
        "var pid=btn.dataset.pid;"
        "var q=QMAP[pid];"
        "if(!q)return;"
        "quoteDiv.querySelector('.s1-qpid').textContent=pid+' \u00b7 '+q.lens;"
        "quoteDiv.querySelector('.s1-qshort').textContent='\u201c'+q.short+'\u201d';"
        "var fullEl=quoteDiv.querySelector('.s1-qfull');"
        "if(q.full&&q.full!==q.short){fullEl.textContent=q.full;fullEl.style.display='block';}"
        "else{fullEl.style.display='none';}"
        "quoteDiv.querySelector('.s1-qref').textContent=q.ref||'';"
        "quoteDiv.style.display='block';"
        "if(hint)hint.style.display='none';"
        "}"
        "block.querySelectorAll('.s1-dot').forEach(function(btn){"
        "btn.addEventListener('click',function(){"
        "if(activeBtn===btn)return;"
        "showQuote(btn);"
        "});"
        "});"
        "document.querySelectorAll('.pid-ref').forEach(function(span){"
        "var pids=(span.dataset.pids||'').split(',').map(function(s){return s.trim();});"
        "var relevant=pids.filter(function(p){return S1PIDS.has(p);});"
        "if(!relevant.length)return;"
        "span.addEventListener('click',function(){"
        "var first=relevant[0];"
        "var dot=block.querySelector('.s1-dot[data-pid=\"'+first+'\"]');"
        "if(dot)showQuote(dot);"
        "});"
        "});"
        "})();"
    )

    return (
        f'<section id="{block_id}" class="s1-dotplot-block">\n'
        f'<style>\n{css}\n</style>\n'
        f'<div class="s1-plot-side">\n{dot_rows_html}\n{legend_html}\n</div>\n'
        f'<div class="s1-quote-side">\n'
        f'<div id="{block_id}-quote" class="s1-quote-panel" style="display:none">'
        f'<p class="s1-qpid"></p>'
        f'<p class="s1-qshort"></p>'
        f'<p class="s1-qfull"></p>'
        f'<p class="s1-qref"></p>'
        f'</div>\n'
        f'<p class="s1-hint">Ch\u1ecdn m\u1ed9t participant \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
        f'</div>\n'
        f'<script>\n{js}\n</script>\n'
        f'</section>\n'
    )


def render_s2_dotplot_interactive(quotes_df, participants_df):
    """S2 Layer 2: interactive dot plot (60%) + quote panel (40%). Self-contained HTML."""
    GROUP_MAP = {
        "P03": "Nhận ra thiếu",
        "P10": "Nhận ra thiếu",
        "P07": "Muốn tích hợp đúng cách",
        "P11": "Muốn tích hợp đúng cách",
        "P12": "Ẩm thực gắn với cộng đồng",
        "P14": "Ẩm thực gắn với cộng đồng",
    }
    GROUP_COLORS = {
        "Nhận ra thiếu":             {"main": "#C4A027", "dark": "#8B7219"},
        "Muốn tích hợp đúng cách":   {"main": "#CF7A3A", "dark": "#9B5B28"},
        "Ẩm thực gắn với cộng đồng": {"main": "#8B6040", "dark": "#6B4A30"},
    }
    GROUP_ORDER = [
        "Nhận ra thiếu",
        "Muốn tích hợp đúng cách",
        "Ẩm thực gắn với cộng đồng",
    ]
    LENS_SHAPE = {"customer": "circle", "industry": "square", "lead_user": "diamond"}
    block_id = "s2-dotplot"

    s2_q = (
        quotes_df[quotes_df["pattern_id"] == "S2"]
        .merge(participants_df[["pid", "lens"]], on="pid", how="left")
        .sort_values("pid")
    )

    rows_js = []
    seen_pid = set()
    for _, r in s2_q.iterrows():
        pid = str(r["pid"])
        if pid in seen_pid:
            continue
        seen_pid.add(pid)
        rows_js.append({
            "pid": pid,
            "lens": str(r["lens"]) if pd.notna(r.get("lens")) else "",
            "confidence": str(r["confidence_level"]) if pd.notna(r.get("confidence_level")) else "",
            "short": str(r["quote_short"]) if pd.notna(r.get("quote_short")) else "",
            "full": str(r["quote_full"]) if pd.notna(r.get("quote_full")) else "",
            "ref": str(r["ref_id"]) if pd.notna(r.get("ref_id")) else "",
        })
    quotes_json = json.dumps(rows_js, ensure_ascii=False).replace("</", "<\\/")
    s2_pids_json = json.dumps(list(GROUP_MAP.keys()))

    group_pids = {g: [] for g in GROUP_ORDER}
    placed_pids = set()
    for _, r in s2_q.iterrows():
        pid = str(r["pid"])
        if pid in placed_pids:
            continue
        lens = str(r["lens"]) if pd.notna(r.get("lens")) else "customer"
        if pid in GROUP_MAP:
            group_pids[GROUP_MAP[pid]].append((pid, lens))
            placed_pids.add(pid)

    dot_rows_html = ""
    for g in GROUP_ORDER:
        colors = GROUP_COLORS[g]
        dots_html = ""
        for pid, lens in group_pids[g]:
            shape = LENS_SHAPE.get(lens, "circle")
            dots_html += (
                f'<button class="s2-dot s2-dot--{shape}" data-pid="{pid}"'
                f' style="--dot-main:{colors["main"]};--dot-dark:{colors["dark"]}"'
                f' aria-label="{pid}" type="button">'
                f'<span class="s2-dot-shape"></span>'
                f'<span class="s2-dot-label">{pid}</span>'
                f'</button>'
            )
        dot_rows_html += (
            f'<div class="s2-group-row">'
            f'<span class="s2-group-label">{html.escape(g)}</span>'
            f'<div class="s2-dots">{dots_html}</div>'
            f'</div>'
        )

    legend_html = (
        '<div class="s2-legend">'
        '<span class="s2-legend-item">'
        '<span class="s2-leg s2-leg--circle"></span>customer</span>'
        '<span class="s2-legend-item">'
        '<span class="s2-leg s2-leg--square"></span>industry</span>'
        '<span class="s2-legend-item">'
        '<span class="s2-leg s2-leg--diamond"></span>lead user</span>'
        '</div>'
    )

    css = (
        f"#{block_id} "
        "{display:grid;grid-template-columns:3fr 2fr;gap:1.5rem;align-items:start;margin:1.5rem 0;}"
        ".s2-plot-side{padding:0.25rem 0;}"
        ".s2-group-row{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.9rem;}"
        ".s2-group-label{min-width:11rem;font-size:0.875rem;color:var(--ink,#2c2c2c);line-height:1.3;}"
        ".s2-dots{display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap;}"
        ".s2-dot{background:none;border:none;padding:0.2rem 0.15rem;cursor:pointer;"
        "display:flex;flex-direction:column;align-items:center;gap:0.18rem;outline:none;}"
        ".s2-dot-shape{width:20px;height:20px;background:var(--dot-main);"
        "display:block;transition:filter 0.15s;}"
        ".s2-dot--circle .s2-dot-shape{border-radius:50%;}"
        ".s2-dot--square .s2-dot-shape{border-radius:2px;}"
        ".s2-dot--diamond .s2-dot-shape{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".s2-dot:hover .s2-dot-shape,.s2-dot.is-active .s2-dot-shape{"
        "filter:drop-shadow(0 0 5px var(--dot-dark)) brightness(1.12);}"
        ".s2-dot-label{font-size:0.72rem;color:var(--muted,#888);line-height:1;}"
        ".s2-dot.is-active .s2-dot-label{color:var(--ink,#2c2c2c);font-weight:600;}"
        ".s2-legend{display:flex;gap:1rem;margin-top:0.6rem;padding-top:0.5rem;"
        "border-top:1px solid var(--line,#d0ccc8);}"
        ".s2-legend-item{display:flex;align-items:center;gap:0.35rem;"
        "font-size:0.78rem;color:var(--muted,#888);}"
        ".s2-leg{width:11px;height:11px;background:var(--muted,#888);display:inline-block;}"
        ".s2-leg--circle{border-radius:50%;}"
        ".s2-leg--square{border-radius:2px;}"
        ".s2-leg--diamond{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".s2-quote-side{min-height:7rem;}"
        ".s2-hint{font-size:0.875rem;color:var(--muted,#888);font-style:italic;margin:0.5rem 0 0;}"
        ".s2-quote-panel{background:var(--bg-soft,#f7f7f5);border-radius:0.7rem;padding:1rem 1.1rem;}"
        ".s2-qpid{font-size:0.78rem;font-weight:600;color:var(--muted,#888);"
        "margin:0 0 0.4rem;text-transform:uppercase;letter-spacing:0.03em;}"
        ".s2-qshort{font-size:0.9rem;font-weight:500;color:var(--ink,#2c2c2c);margin:0;font-style:italic;}"
        ".s2-qfull{font-size:0.82rem;color:var(--muted,#888);margin:0.5rem 0 0.3rem;"
        "border-top:1px solid var(--line,#d0ccc8);padding-top:0.5rem;}"
        ".s2-qref{font-size:0.73rem;color:var(--muted,#888);margin:0.2rem 0 0;"
        "font-family:monospace;opacity:0.75;}"
    )

    js = (
        "(function(){"
        f"var QUOTES={quotes_json};"
        f"var S2PIDS=new Set({s2_pids_json});"
        f"var block=document.getElementById('{block_id}');"
        "if(!block)return;"
        f"var quoteDiv=document.getElementById('{block_id}-quote');"
        "var hint=block.querySelector('.s2-hint');"
        "var activeBtn=null;"
        "var QMAP={};"
        "QUOTES.forEach(function(q){QMAP[q.pid]=q;});"
        "function showQuote(btn){"
        "if(activeBtn)activeBtn.classList.remove('is-active');"
        "activeBtn=btn;"
        "btn.classList.add('is-active');"
        "var pid=btn.dataset.pid;"
        "var q=QMAP[pid];"
        "if(!q)return;"
        "quoteDiv.querySelector('.s2-qpid').textContent=pid+' \u00b7 '+q.lens;"
        "quoteDiv.querySelector('.s2-qshort').textContent='\u201c'+q.short+'\u201d';"
        "var fullEl=quoteDiv.querySelector('.s2-qfull');"
        "if(q.full&&q.full!==q.short){fullEl.textContent=q.full;fullEl.style.display='block';}"
        "else{fullEl.style.display='none';}"
        "quoteDiv.querySelector('.s2-qref').textContent=q.ref||'';"
        "quoteDiv.style.display='block';"
        "if(hint)hint.style.display='none';"
        "}"
        "block.querySelectorAll('.s2-dot').forEach(function(btn){"
        "btn.addEventListener('click',function(){"
        "if(activeBtn===btn)return;"
        "showQuote(btn);"
        "});"
        "});"
        "document.querySelectorAll('.pid-ref').forEach(function(span){"
        "var pids=(span.dataset.pids||'').split(',').map(function(s){return s.trim();});"
        "var relevant=pids.filter(function(p){return S2PIDS.has(p);});"
        "if(!relevant.length)return;"
        "span.addEventListener('click',function(){"
        "var first=relevant[0];"
        "var dot=block.querySelector('.s2-dot[data-pid=\"'+first+'\"]');"
        "if(dot)showQuote(dot);"
        "});"
        "});"
        "})();"
    )

    return (
        f'<section id="{block_id}" class="s2-dotplot-block">\n'
        f'<style>\n{css}\n</style>\n'
        f'<div class="s2-plot-side">\n{dot_rows_html}\n{legend_html}\n</div>\n'
        f'<div class="s2-quote-side">\n'
        f'<div id="{block_id}-quote" class="s2-quote-panel" style="display:none">'
        f'<p class="s2-qpid"></p>'
        f'<p class="s2-qshort"></p>'
        f'<p class="s2-qfull"></p>'
        f'<p class="s2-qref"></p>'
        f'</div>\n'
        f'<p class="s2-hint">Ch\u1ecdn m\u1ed9t participant \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
        f'</div>\n'
        f'<script>\n{js}\n</script>\n'
        f'</section>\n'
    )


def render_p5_dotplot_interactive(quotes_df, participants_df):
    """P5 Layer 2: interactive dot plot (60%) + quote panel (40%). Self-contained HTML."""
    GROUP_MAP = {
        "P07": "Chưa đủ thương hiệu điểm đến",
        "P08": "Chưa đủ thương hiệu điểm đến",
        "P09": "Chưa đủ thương hiệu điểm đến",
        "P14": "Rào cản địa lý",
        "P04": "Tín hiệu sớm / góc ngành",
        "P12": "Tín hiệu sớm / góc ngành",
        "P13": "Tín hiệu sớm / góc ngành",
    }
    GROUP_COLORS = {
        "Chưa đủ thương hiệu điểm đến": {"main": "#C97D2E", "dark": "#8B5A1E"},
        "Rào cản địa lý":               {"main": "#4B7B9E", "dark": "#2F5A7A"},
        "Tín hiệu sớm / góc ngành":     {"main": "#8C9BAB", "dark": "#6B7A8A"},
    }
    GROUP_ORDER = [
        "Chưa đủ thương hiệu điểm đến",
        "Rào cản địa lý",
        "Tín hiệu sớm / góc ngành",
    ]
    WARN_PIDS = {"P13"}
    LENS_SHAPE = {"customer": "circle", "industry": "square", "lead_user": "diamond"}
    block_id = "p5-dotplot"

    p5_q = (
        quotes_df[quotes_df["pattern_id"] == "P5"]
        .merge(participants_df[["pid", "lens"]], on="pid", how="left")
        .sort_values("pid")
    )

    rows_js = []
    for _, r in p5_q.iterrows():
        pid = str(r["pid"])
        row = {
            "pid": pid,
            "lens": str(r["lens"]) if pd.notna(r.get("lens")) else "",
            "confidence": str(r["confidence_level"]) if pd.notna(r.get("confidence_level")) else "",
            "short": str(r["quote_short"]) if pd.notna(r.get("quote_short")) else "",
            "full": str(r["quote_full"]) if pd.notna(r.get("quote_full")) else "",
            "ref": str(r["ref_id"]) if pd.notna(r.get("ref_id")) else "",
        }
        if pid in WARN_PIDS:
            row["warn"] = True
        rows_js.append(row)
    quotes_json = json.dumps(rows_js, ensure_ascii=False).replace("</", "<\\/")
    p5_pids_json = json.dumps(list(GROUP_MAP.keys()))

    group_pids = {g: [] for g in GROUP_ORDER}
    for _, r in p5_q.iterrows():
        pid = str(r["pid"])
        lens = str(r["lens"]) if pd.notna(r.get("lens")) else "customer"
        if pid in GROUP_MAP:
            group_pids[GROUP_MAP[pid]].append((pid, lens))

    dot_rows_html = ""
    for g in GROUP_ORDER:
        colors = GROUP_COLORS[g]
        dots_html = ""
        for pid, lens in group_pids[g]:
            shape = LENS_SHAPE.get(lens, "circle")
            dots_html += (
                f'<button class="p5-dot p5-dot--{shape}" data-pid="{pid}"'
                f' style="--dot-main:{colors["main"]};--dot-dark:{colors["dark"]}"'
                f' aria-label="{pid}" type="button">'
                f'<span class="p5-dot-shape"></span>'
                f'<span class="p5-dot-label">{pid}</span>'
                f'</button>'
            )
        dot_rows_html += (
            f'<div class="p5-group-row">'
            f'<span class="p5-group-label">{html.escape(g)}</span>'
            f'<div class="p5-dots">{dots_html}</div>'
            f'</div>'
        )

    legend_html = (
        '<div class="p5-legend">'
        '<span class="p5-legend-item">'
        '<span class="p5-leg p5-leg--circle"></span>customer</span>'
        '<span class="p5-legend-item">'
        '<span class="p5-leg p5-leg--square"></span>industry</span>'
        '<span class="p5-legend-item">'
        '<span class="p5-leg p5-leg--diamond"></span>lead user</span>'
        '</div>'
    )

    css = (
        f"#{block_id} "
        "{display:grid;grid-template-columns:3fr 2fr;gap:1.5rem;align-items:start;margin:1.5rem 0;}"
        ".p5-plot-side{padding:0.25rem 0;}"
        ".p5-group-row{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.9rem;}"
        ".p5-group-label{min-width:11rem;font-size:0.875rem;color:var(--ink,#2c2c2c);line-height:1.3;}"
        ".p5-dots{display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap;}"
        ".p5-dot{background:none;border:none;padding:0.2rem 0.15rem;cursor:pointer;"
        "display:flex;flex-direction:column;align-items:center;gap:0.18rem;outline:none;}"
        ".p5-dot-shape{width:20px;height:20px;background:var(--dot-main);"
        "display:block;transition:filter 0.15s;}"
        ".p5-dot--circle .p5-dot-shape{border-radius:50%;}"
        ".p5-dot--square .p5-dot-shape{border-radius:2px;}"
        ".p5-dot--diamond .p5-dot-shape{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".p5-dot:hover .p5-dot-shape,.p5-dot.is-active .p5-dot-shape{"
        "filter:drop-shadow(0 0 5px var(--dot-dark)) brightness(1.12);}"
        ".p5-dot-label{font-size:0.72rem;color:var(--muted,#888);line-height:1;}"
        ".p5-dot.is-active .p5-dot-label{color:var(--ink,#2c2c2c);font-weight:600;}"
        ".p5-legend{display:flex;gap:1rem;margin-top:0.6rem;padding-top:0.5rem;"
        "border-top:1px solid var(--line,#d0ccc8);}"
        ".p5-legend-item{display:flex;align-items:center;gap:0.35rem;"
        "font-size:0.78rem;color:var(--muted,#888);}"
        ".p5-leg{width:11px;height:11px;background:var(--muted,#888);display:inline-block;}"
        ".p5-leg--circle{border-radius:50%;}"
        ".p5-leg--square{border-radius:2px;}"
        ".p5-leg--diamond{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".p5-quote-side{min-height:7rem;}"
        ".p5-hint{font-size:0.875rem;color:var(--muted,#888);font-style:italic;margin:0.5rem 0 0;}"
        ".p5-quote-panel{background:var(--bg-soft,#f7f7f5);border-radius:0.7rem;padding:1rem 1.1rem;}"
        ".p5-qpid{font-size:0.78rem;font-weight:600;color:var(--muted,#888);"
        "margin:0 0 0.4rem;text-transform:uppercase;letter-spacing:0.03em;}"
        ".p5-qshort{font-size:0.9rem;font-weight:500;color:var(--ink,#2c2c2c);margin:0;font-style:italic;}"
        ".p5-qfull{font-size:0.82rem;color:var(--muted,#888);margin:0.5rem 0 0.3rem;"
        "border-top:1px solid var(--line,#d0ccc8);padding-top:0.5rem;}"
        ".p5-qref{font-size:0.73rem;color:var(--muted,#888);margin:0.2rem 0 0;"
        "font-family:monospace;opacity:0.75;}"
        ".p5-qwarn{font-size:0.8rem;color:#8B5A1E;background:#FFF8F0;"
        "border:1px solid #E8C9A0;border-radius:0.5rem;padding:0.55rem 0.7rem;"
        "margin:0.6rem 0 0;line-height:1.4;}"
    )

    warn_text = (
        "\u26a0\ufe0f Q060 \u0111ang ch\u1edd x\u00e1c minh transcript th\u00f4. "
        "K\u1ebft lu\u1eadn t\u1eeb tr\u00edch d\u1eabn n\u00e0y c\u1ea7n \u0111\u1ecdc c\u00f3 ch\u00fa \u00fd."
    )

    js = (
        "(function(){"
        f"var QUOTES={quotes_json};"
        f"var P5PIDS=new Set({p5_pids_json});"
        f"var block=document.getElementById('{block_id}');"
        "if(!block)return;"
        f"var quoteDiv=document.getElementById('{block_id}-quote');"
        "var hint=block.querySelector('.p5-hint');"
        "var activeBtn=null;"
        "var QMAP={};"
        "QUOTES.forEach(function(q){QMAP[q.pid]=q;});"
        "function showQuote(btn){"
        "if(activeBtn)activeBtn.classList.remove('is-active');"
        "activeBtn=btn;"
        "btn.classList.add('is-active');"
        "var pid=btn.dataset.pid;"
        "var q=QMAP[pid];"
        "if(!q)return;"
        "quoteDiv.querySelector('.p5-qpid').textContent=pid+' \u00b7 '+q.lens;"
        "quoteDiv.querySelector('.p5-qshort').textContent='\u201c'+q.short+'\u201d';"
        "var fullEl=quoteDiv.querySelector('.p5-qfull');"
        "if(q.full&&q.full!==q.short){fullEl.textContent=q.full;fullEl.style.display='block';}"
        "else{fullEl.style.display='none';}"
        "quoteDiv.querySelector('.p5-qref').textContent=q.ref||'';"
        "var warnEl=quoteDiv.querySelector('.p5-qwarn');"
        f"if(q.warn){{warnEl.textContent='{warn_text}';warnEl.style.display='block';}}"
        "else{warnEl.style.display='none';}"
        "quoteDiv.style.display='block';"
        "if(hint)hint.style.display='none';"
        "}"
        "block.querySelectorAll('.p5-dot').forEach(function(btn){"
        "btn.addEventListener('click',function(){"
        "if(activeBtn===btn)return;"
        "showQuote(btn);"
        "});"
        "});"
        "document.querySelectorAll('.pid-ref').forEach(function(span){"
        "var pids=(span.dataset.pids||'').split(',').map(function(s){return s.trim();});"
        "var relevant=pids.filter(function(p){return P5PIDS.has(p);});"
        "if(!relevant.length)return;"
        "span.addEventListener('click',function(){"
        "var first=relevant[0];"
        "var dot=block.querySelector('.p5-dot[data-pid=\"'+first+'\"]');"
        "if(dot)showQuote(dot);"
        "});"
        "});"
        "})();"
    )

    return (
        f'<section id="{block_id}" class="p5-dotplot-block">\n'
        f'<style>\n{css}\n</style>\n'
        f'<div class="p5-plot-side">\n{dot_rows_html}\n{legend_html}\n</div>\n'
        f'<div class="p5-quote-side">\n'
        f'<div id="{block_id}-quote" class="p5-quote-panel" style="display:none">'
        f'<p class="p5-qpid"></p>'
        f'<p class="p5-qshort"></p>'
        f'<p class="p5-qfull"></p>'
        f'<p class="p5-qref"></p>'
        f'<p class="p5-qwarn" style="display:none"></p>'
        f'</div>\n'
        f'<p class="p5-hint">Ch\u1ecdn m\u1ed9t participant \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
        f'</div>\n'
        f'<script>\n{js}\n</script>\n'
        f'</section>\n'
    )


def render_p4_dotplot_interactive(quotes_df, participants_df):
    """P4 Layer 2: interactive dot plot (60%) + quote panel (40%). Self-contained HTML."""
    GROUP_MAP = {
        "P01": "Phản đối rõ", "P06": "Phản đối rõ", "P14": "Phản đối rõ",
        "P08": "Chấp nhận có điều kiện", "P11": "Chấp nhận có điều kiện",
        "P07": "Định nghĩa lại", "P09": "Định nghĩa lại",
    }
    GROUP_COLORS = {
        "Phản đối rõ":            {"main": "#D85A30", "dark": "#b54a27"},
        "Chấp nhận có điều kiện": {"main": "#EF9F27", "dark": "#c77e0f"},
        "Định nghĩa lại":         {"main": "#1D9E75", "dark": "#157a59"},
    }
    GROUP_ORDER = ["Phản đối rõ", "Chấp nhận có điều kiện", "Định nghĩa lại"]
    LENS_SHAPE = {"customer": "circle", "industry": "square", "lead_user": "diamond"}
    block_id = "p4-dotplot"

    p4_q = (
        quotes_df[quotes_df["pattern_id"] == "P4"]
        .merge(participants_df[["pid", "lens"]], on="pid", how="left")
        .sort_values("pid")
    )

    rows_js = []
    for _, r in p4_q.iterrows():
        rows_js.append({
            "pid": str(r["pid"]),
            "lens": str(r["lens"]) if pd.notna(r.get("lens")) else "",
            "confidence": str(r["confidence_level"]) if pd.notna(r.get("confidence_level")) else "",
            "short": str(r["quote_short"]) if pd.notna(r.get("quote_short")) else "",
            "full": str(r["quote_full"]) if pd.notna(r.get("quote_full")) else "",
            "ref": str(r["ref_id"]) if pd.notna(r.get("ref_id")) else "",
        })
    quotes_json = json.dumps(rows_js, ensure_ascii=False).replace("</", "<\\/")
    p4_pids_json = json.dumps(list(GROUP_MAP.keys()))

    group_pids = {g: [] for g in GROUP_ORDER}
    for _, r in p4_q.iterrows():
        pid = str(r["pid"])
        lens = str(r["lens"]) if pd.notna(r.get("lens")) else "customer"
        if pid in GROUP_MAP:
            group_pids[GROUP_MAP[pid]].append((pid, lens))

    dot_rows_html = ""
    for g in GROUP_ORDER:
        colors = GROUP_COLORS[g]
        dots_html = ""
        for pid, lens in group_pids[g]:
            shape = LENS_SHAPE.get(lens, "circle")
            dots_html += (
                f'<button class="p4-dot p4-dot--{shape}" data-pid="{pid}"'
                f' style="--dot-main:{colors["main"]};--dot-dark:{colors["dark"]}"'
                f' aria-label="{pid}" type="button">'
                f'<span class="p4-dot-shape"></span>'
                f'<span class="p4-dot-label">{pid}</span>'
                f'</button>'
            )
        dot_rows_html += (
            f'<div class="p4-group-row">'
            f'<span class="p4-group-label">{html.escape(g)}</span>'
            f'<div class="p4-dots">{dots_html}</div>'
            f'</div>'
        )

    legend_html = (
        '<div class="p4-legend">'
        '<span class="p4-legend-item">'
        '<span class="p4-leg p4-leg--circle"></span>customer</span>'
        '<span class="p4-legend-item">'
        '<span class="p4-leg p4-leg--square"></span>industry</span>'
        '<span class="p4-legend-item">'
        '<span class="p4-leg p4-leg--diamond"></span>lead user</span>'
        '</div>'
    )

    css = (
        f"#{block_id} "
        "{display:grid;grid-template-columns:3fr 2fr;gap:1.5rem;align-items:start;margin:1.5rem 0;}"
        ".p4-plot-side{padding:0.25rem 0;}"
        ".p4-group-row{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.9rem;}"
        ".p4-group-label{min-width:11rem;font-size:0.875rem;color:var(--ink,#2c2c2c);line-height:1.3;}"
        ".p4-dots{display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap;}"
        ".p4-dot{background:none;border:none;padding:0.2rem 0.15rem;cursor:pointer;"
        "display:flex;flex-direction:column;align-items:center;gap:0.18rem;outline:none;}"
        ".p4-dot-shape{width:20px;height:20px;background:var(--dot-main);"
        "display:block;transition:filter 0.15s;}"
        ".p4-dot--circle .p4-dot-shape{border-radius:50%;}"
        ".p4-dot--square .p4-dot-shape{border-radius:2px;}"
        ".p4-dot--diamond .p4-dot-shape{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".p4-dot:hover .p4-dot-shape,.p4-dot.is-active .p4-dot-shape{"
        "filter:drop-shadow(0 0 5px var(--dot-dark)) brightness(1.12);}"
        ".p4-dot-label{font-size:0.72rem;color:var(--muted,#888);line-height:1;}"
        ".p4-dot.is-active .p4-dot-label{color:var(--ink,#2c2c2c);font-weight:600;}"
        ".p4-legend{display:flex;gap:1rem;margin-top:0.6rem;padding-top:0.5rem;"
        "border-top:1px solid var(--line,#d0ccc8);}"
        ".p4-legend-item{display:flex;align-items:center;gap:0.35rem;"
        "font-size:0.78rem;color:var(--muted,#888);}"
        ".p4-leg{width:11px;height:11px;background:var(--muted,#888);display:inline-block;}"
        ".p4-leg--circle{border-radius:50%;}"
        ".p4-leg--square{border-radius:2px;}"
        ".p4-leg--diamond{clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);}"
        ".p4-quote-side{min-height:7rem;}"
        ".p4-hint{font-size:0.875rem;color:var(--muted,#888);font-style:italic;margin:0.5rem 0 0;}"
        ".p4-quote-panel{background:var(--bg-soft,#f7f7f5);border-radius:0.7rem;padding:1rem 1.1rem;}"
        ".p4-qpid{font-size:0.78rem;font-weight:600;color:var(--muted,#888);"
        "margin:0 0 0.4rem;text-transform:uppercase;letter-spacing:0.03em;}"
        ".p4-qshort{font-size:0.9rem;font-weight:500;color:var(--ink,#2c2c2c);margin:0;font-style:italic;}"
        ".p4-qfull{font-size:0.82rem;color:var(--muted,#888);margin:0.5rem 0 0.3rem;"
        "border-top:1px solid var(--line,#d0ccc8);padding-top:0.5rem;}"
        ".p4-qref{font-size:0.73rem;color:var(--muted,#888);margin:0.2rem 0 0;"
        "font-family:monospace;opacity:0.75;}"
    )

    js = (
        "(function(){"
        f"var QUOTES={quotes_json};"
        f"var P4PIDS=new Set({p4_pids_json});"
        f"var block=document.getElementById('{block_id}');"
        "if(!block)return;"
        f"var quoteDiv=document.getElementById('{block_id}-quote');"
        "var hint=block.querySelector('.p4-hint');"
        "var activeBtn=null;"
        "var QMAP={};"
        "QUOTES.forEach(function(q){QMAP[q.pid]=q;});"
        "function showQuote(btn){"
        "if(activeBtn)activeBtn.classList.remove('is-active');"
        "activeBtn=btn;"
        "btn.classList.add('is-active');"
        "var pid=btn.dataset.pid;"
        "var q=QMAP[pid];"
        "if(!q)return;"
        "quoteDiv.querySelector('.p4-qpid').textContent=pid+' \u00b7 '+q.lens;"
        "quoteDiv.querySelector('.p4-qshort').textContent='\u201c'+q.short+'\u201d';"
        "var fullEl=quoteDiv.querySelector('.p4-qfull');"
        "if(q.full&&q.full!==q.short){fullEl.textContent=q.full;fullEl.style.display='block';}"
        "else{fullEl.style.display='none';}"
        "quoteDiv.querySelector('.p4-qref').textContent=q.ref||'';"
        "quoteDiv.style.display='block';"
        "if(hint)hint.style.display='none';"
        "}"
        "block.querySelectorAll('.p4-dot').forEach(function(btn){"
        "btn.addEventListener('click',function(){"
        "if(activeBtn===btn)return;"
        "showQuote(btn);"
        "});"
        "});"
        "document.querySelectorAll('.pid-ref').forEach(function(span){"
        "var pids=(span.dataset.pids||'').split(',').map(function(s){return s.trim();});"
        "var relevant=pids.filter(function(p){return P4PIDS.has(p);});"
        "if(!relevant.length)return;"
        "span.addEventListener('click',function(){"
        "var first=relevant[0];"
        "var dot=block.querySelector('.p4-dot[data-pid=\"'+first+'\"]');"
        "if(dot)showQuote(dot);"
        "});"
        "});"
        "})();"
    )

    return (
        f'<section id="{block_id}" class="p4-dotplot-block">\n'
        f'<style>\n{css}\n</style>\n'
        f'<div class="p4-plot-side">\n{dot_rows_html}\n{legend_html}\n</div>\n'
        f'<div class="p4-quote-side">\n'
        f'<div id="{block_id}-quote" class="p4-quote-panel" style="display:none">'
        f'<p class="p4-qpid"></p>'
        f'<p class="p4-qshort"></p>'
        f'<p class="p4-qfull"></p>'
        f'<p class="p4-qref"></p>'
        f'</div>\n'
        f'<p class="p4-hint">Ch\u1ecdn m\u1ed9t participant \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
        f'</div>\n'
        f'<script>\n{js}\n</script>\n'
        f'</section>\n'
    )


def segment_breakdown(dimension, participants_df):
    """Count participants by dimension."""
    allowed = {"convert_type", "lens", "experience", "residence", "age_group"}
    if dimension not in allowed:
        raise ValueError(f"dimension phải thuộc {allowed}, không phải {dimension!r}")
    total = len(participants_df)
    s = participants_df[dimension].fillna("(rỗng)").astype(str)
    counts = s.value_counts()
    if dimension == "convert_type":
        order = [c for c in CONVERT_TYPE_ORDER if c in counts.index]
        order += [c for c in counts.index if c not in CONVERT_TYPE_ORDER]
        counts = counts.reindex(order)
    rows = [(val, int(n), f"{int(n)}/{total}") for val, n in counts.items()]
    return _md_table([dimension, "n", "share"], rows)


def participants_table(participants_df, sort_by="convert_type"):
    """Participants: pid | experience | lens | convert_type | nghề (generalize) | spend | WTP."""
    df = participants_df.copy()
    if sort_by == "convert_type":
        df["_ord"] = df["convert_type"].map(_CONVERT_ORDER).fillna(99)
        df = df.sort_values(["_ord", "pid"]).drop(columns="_ord")
    elif sort_by == "pid":
        df = df.sort_values("pid")
    else:
        df = df.sort_values(sort_by)
    rows = []
    for _, r in df.iterrows():
        rows.append((
            r["pid"],
            r["experience"],
            r["lens"],
            r["convert_type"],
            OCCUPATION_GENERALIZED.get(r["pid"], "(missing)"),
            r["travel_spend_range"] if pd.notna(r["travel_spend_range"]) else "",
            r["acceptable_tour_price"] if pd.notna(r["acceptable_tour_price"]) else "",
        ))
    return _md_table(
        ["pid", "experience", "lens", "convert_type", "Nghề", "Spend", "WTP"], rows
    )


def _wtp_band(raw):
    """Band WTP: chỉ điền chỗ nói rõ, để trống chỗ 'không hỏi'/rỗng."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    low = s.lower()
    if "không hỏi" in low:
        return ""
    return s


def spend_vs_wtp_table(participants_df):
    """pid | nghề | spend | WTP raw | band WTP. KHÔNG tính mean."""
    df = participants_df.copy()
    df["_ord"] = df["convert_type"].map(_CONVERT_ORDER).fillna(99)
    df = df.sort_values(["_ord", "pid"])
    rows = []
    for _, r in df.iterrows():
        spend = r["travel_spend_range"] if pd.notna(r["travel_spend_range"]) else ""
        wtp_raw = r["acceptable_tour_price"] if pd.notna(r["acceptable_tour_price"]) else ""
        rows.append((
            r["pid"],
            OCCUPATION_GENERALIZED.get(r["pid"], "(missing)"),
            spend,
            wtp_raw,
            _wtp_band(wtp_raw),
        ))
    return _md_table(
        ["pid", "Nghề", "Spend (thật)", "WTP (raw)", "Band WTP"], rows
    )


def study_integrity_summary(participants_df, quotes_df, records_df=None, expected_participants=None, expected_quotes=None, expected_records=None):
    """Render current CSV shape and optional expected compiled-record checks."""
    current_participants = len(participants_df)
    current_quotes = len(quotes_df)
    rows = [
        ("participants.csv", current_participants, expected_participants or "", "OK" if not expected_participants or current_participants == expected_participants else "Needs reconciliation"),
        ("quotes.csv", current_quotes, expected_quotes or "", "OK" if not expected_quotes or current_quotes == expected_quotes else "Needs reconciliation"),
    ]
    if records_df is not None:
        current_records = len(records_df)
        rows.append((
            "records.csv",
            current_records,
            expected_records or "",
            "OK" if not expected_records or current_records == expected_records else "Needs reconciliation",
        ))
    return _md_table(["Source", "Current rows", "Expected rows", "Status"], rows)


def sample_overview_table(participants_df):
    """Compact sample overview across core anonymized fields."""
    rows = []
    for dimension in ("experience", "lens", "residence", "convert_type"):
        counts = participants_df[dimension].fillna("(rỗng)").astype(str).value_counts()
        for value, n in counts.items():
            rows.append((dimension, value, int(n), f"{int(n)}/{len(participants_df)}"))
    return _md_table(["Dimension", "Value", "n", "Share"], rows)


def quote_evidence_table(quotes_df, participants_df, pattern_id=None, theme=None, subtheme=None, limit=3):
    """Render quote evidence with P-code and ref_id only."""
    df = quotes_df.copy()
    if pattern_id is not None:
        df = df[df["pattern_id"] == pattern_id]
    if theme is not None:
        df = df[df["theme"] == theme]
    if subtheme is not None:
        df = df[df["subtheme"] == subtheme]
    df = df.sort_values(["pid", "quote_id"]).head(limit)
    rows = []
    valid_pids = set(participants_df["pid"].astype(str))
    for _, r in df.iterrows():
        pid = str(r["pid"])
        rows.append((
            pid if pid in valid_pids else f"{pid} (pid missing)",
            r["quote_short"] if pd.notna(r["quote_short"]) else r["quote_full"],
            r["ref_id"] if pd.notna(r["ref_id"]) else "",
        ))
    if not rows:
        rows = [("—", "No coded evidence in quotes.csv", "—")]
    return _md_table(["pid", "Evidence", "ref_id"], rows)


# ----------------------------------------------------------------- public report visuals

_VI_REPLACEMENTS = {
    "—": " / ",
    "â€”": " / ",
    "tour": "chuyến đi",
    "Tour": "Chuyến đi",
    "WTP": "giá có thể chấp nhận",
    "Spend": "mức chi",
    "Hypothesis": "Giả thuyết",
    "lead_user": "người dùng dẫn dắt",
    "industry": "góc nhìn ngành",
    "customer": "khách tiềm năng",
    "da_tung": "đã có kinh nghiệm",
    "chua_tung": "chưa hoặc ít kinh nghiệm",
    "true_target": "phù hợp rõ",
    "conditional": "phù hợp có điều kiện",
    "passive": "bị động",
    "harder": "khó chuyển đổi hơn",
    "future": "cần thêm dữ liệu",
    "non_target": "không phải nhóm ưu tiên",
    "NGO": "tổ chức phi chính phủ",
    "Founder startup": "nhà sáng lập doanh nghiệp",
    "startup": "doanh nghiệp khởi nghiệp",
    "Sales": "nhân viên kinh doanh",
    "agency": "đơn vị dịch vụ",
    "CSR": "trách nhiệm xã hội",
    "outbound": "đưa khách ra nước ngoài",
}


def _plain_vi(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value)
    for old, new in _VI_REPLACEMENTS.items():
        text = text.replace(old, new)
    return " ".join(text.split())


def _e(value):
    return html.escape(_plain_vi(value), quote=True)


def _has_values(df, columns):
    if any(col not in df.columns for col in columns):
        return False
    sub = df[list(columns)].copy()
    not_blank = sub.fillna("").astype(str).apply(lambda s: s.str.strip().ne("")).any().any()
    return bool(not_blank)


_NEEDED_LABELS = {
    "wtp_min": "cận dưới giá có thể chấp nhận",
    "wtp_max": "cận trên giá có thể chấp nhận",
    "interest_score": "điểm quan tâm",
    "prefers_selftour": "ưu tiên đi tự túc",
    "companion_dependent": "phụ thuộc người đi cùng",
    "price_sensitive": "nhạy cảm với giá",
    "experience_over_resort": "ưu tiên trải nghiệm hơn nghỉ dưỡng",
    "cares_about_authenticity": "quan tâm tính chân thực",
    "sustainability_awareness": "mức quen thuộc với du lịch bền vững",
    "price_sensitivity": "mức nhạy cảm với giá",
    "cultural_depth_interest": "mức quan tâm chiều sâu văn hoá",
}


def render_data_placeholder(title, needed):
    """Render placeholder for visual fields that still need manual coding."""
    needed_text = ", ".join(_NEEDED_LABELS.get(col, col) for col in needed)
    return (
        '<div class="mach-viz mach-viz-placeholder">'
        f'<strong>{_e(title)}</strong>'
        '<p>Chưa có dữ liệu phân loại, cần Khanh điền trước khi đọc phần này.</p>'
        f'<p><small>Trường cần điền: {html.escape(needed_text, quote=True)}</small></p>'
        '</div>'
    )


def render_participant_grid(participants_df):
    """Participant grid from anonymized committed data. P-code only."""
    df = participants_df.sort_values("pid").copy()
    cards = []
    for _, row in df.iterrows():
        pid = row["pid"]
        cards.append(
            '<div class="participant-card">'
            f'<strong>{_e(pid)}</strong>'
            f'<small>{_e(row.get("experience", ""))}</small>'
            f'<p>{_e(OCCUPATION_GENERALIZED.get(pid, ""))}</p>'
            f'<p><small>{_e(row.get("convert_type", ""))}</small></p>'
            '</div>'
        )
    return (
        '<div class="mach-viz">'
        '<h4>Lưới người tham gia</h4>'
        '<div class="participant-grid">'
        + "".join(cards)
        + '</div></div>'
    )


def render_pattern_matrix(participants_df, quotes_df):
    """Pattern by participant matrix using coded quote occurrence. Counts only."""
    all_pids = participants_df.sort_values("pid")["pid"].astype(str).tolist()
    order = ["P1", "P2", "P3", "P4", "P5", "P6", "S1", "S2", "H1"]
    cards = []
    for pattern_id in order:
        meta = PATTERN_META[pattern_id]
        occ = pattern_occurrence(pattern_id, quotes_df, participants_df)
        hit_pids = set(occ["pids"])
        dots = []
        for pid in all_pids:
            cls = "pattern-dot pattern-dot-hit" if pid in hit_pids else "pattern-dot"
            dots.append(f'<span class="{cls}">{_e(pid)}</span>')
        confidence = _plain_vi(meta["confidence"])
        if confidence == "Hypothesis":
            confidence = "Giả thuyết"
        cards.append(
            '<div class="pattern-matrix-card">'
            f'<strong>{_e(pattern_id)}. {_e(meta["name"])}</strong>'
            f'<small>{occ["count"]}/{occ["total"]} người / {_e(confidence)}</small>'
            '<div class="pattern-dot-row">'
            + "".join(dots)
            + '</div></div>'
        )
    return (
        '<div class="mach-viz">'
        '<h4>Ma trận tín hiệu theo người tham gia</h4>'
        '<div class="pattern-matrix">'
        + "".join(cards)
        + '</div></div>'
    )


def render_wtp_plot(participants_df):
    needed = ["wtp_min", "wtp_max"]
    if not _has_values(participants_df, needed):
        return render_data_placeholder("Vùng giá có thể chấp nhận", needed)
    rows = []
    df = participants_df.sort_values("pid")
    for _, row in df.iterrows():
        if pd.notna(row.get("wtp_min")) or pd.notna(row.get("wtp_max")):
            rows.append((row["pid"], row.get("wtp_min", ""), row.get("wtp_max", "")))
    return _md_table(["Mã người tham gia", "Cận dưới", "Cận trên"], rows)


def render_behaviour_matrix(participants_df):
    needed = [
        "prefers_selftour",
        "companion_dependent",
        "price_sensitive",
        "experience_over_resort",
        "cares_about_authenticity",
    ]
    if not _has_values(participants_df, needed):
        return render_data_placeholder("Ma trận hành vi du lịch", needed)
    rows = []
    for col in needed:
        s = participants_df[col].fillna("").astype(str).str.strip().str.lower()
        rows.append((col, int(s.isin(["true", "1", "yes", "co", "có"]).sum())))
    return _md_table(["Tín hiệu", "Số người đã mã hoá"], rows)


def render_interest_plot(participants_df):
    needed = ["interest_score"]
    if not _has_values(participants_df, needed):
        return render_data_placeholder("Điểm quan tâm đến chuyến đi", needed)
    rows = []
    for _, row in participants_df.sort_values("pid").iterrows():
        if pd.notna(row.get("interest_score")) and str(row.get("interest_score")).strip():
            rows.append((row["pid"], row.get("interest_score")))
    return _md_table(["Mã người tham gia", "Điểm quan tâm"], rows)


def render_sustainability_buckets(participants_df):
    needed = ["sustainability_awareness"]
    if not _has_values(participants_df, needed):
        return render_data_placeholder("Mức quen thuộc với du lịch bền vững", needed)
    counts = participants_df["sustainability_awareness"].fillna("").astype(str).str.strip()
    counts = counts[counts != ""].value_counts()
    rows = [(label, int(count)) for label, count in counts.items()]
    return _md_table(["Mức quen thuộc", "Số người đã mã hoá"], rows)


def render_archetype_scatter(participants_df):
    needed = ["price_sensitivity", "cultural_depth_interest"]
    if not _has_values(participants_df, needed):
        return render_data_placeholder("Bản đồ nhóm khách theo giá và chiều sâu văn hoá", needed)
    rows = []
    for _, row in participants_df.sort_values("pid").iterrows():
        price = row.get("price_sensitivity", "")
        depth = row.get("cultural_depth_interest", "")
        if str(price).strip() or str(depth).strip():
            rows.append((row["pid"], price, depth))
    return _md_table(["Mã người tham gia", "Nhạy cảm với giá", "Quan tâm chiều sâu văn hoá"], rows)
