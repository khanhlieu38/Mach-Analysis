"""
viz_helpers.py — Compute helpers for MẠCH pretour-research-2026.

Rule #1: số trong báo cáo compute từ CSV, KHÔNG hardcode.
- Total participants = len(participants_df).
- Confidence pattern lấy từ PATTERN_META (sync STUDY_RULES.md mục 5; caveats báo cáo trong STUDY_RULES),
  KHÔNG lấy từ field `confidence_level` của quote (field đó là per-quote, mơ hồ
  để derive pattern-level).
- P-code only. Cột `occupation` committed đã được khái quát hoá.

Báo cáo là prose + markdown table. Không có chart.
"""

import html
import json
import re
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
        "deck_name": "Trải nghiệm còn thụ động",
        "confidence": "Cao",
        "industry_leaning": False,
        "note": (
            "Hình thức quá thụ động, không phải nội dung quá sâu. "
            "Giảm liều, tăng hoạt động tự tay làm."
        ),
    },
    "P2": {
        "name": "Phụ thuộc người đồng hành",
        "deck_name": "Phụ thuộc vào người đi cùng",
        "confidence": "Cao",
        "industry_leaning": False,
        "note": (
            "Rào cản là thiếu đúng người đi cùng, không phải từ chối tour. "
            "Cần mời theo nhóm thay vì để từng người tự đăng ký."
        ),
    },
    "P3": {
        "name": "Nhận diện phân khúc: 'tour cho người khác, không hẳn tôi'",
        "deck_name": "Lệch định vị khách hàng",
        "confidence": "Trung bình",
        "industry_leaning": False,
        "note": (
            "Phân hóa rõ giữa người tự nhận phù hợp và tự loại. Phân khúc "
            "là tư duy, không phải tuổi. Truyền thông nhắm vào thái độ."
        ),
    },
    "P4": {
        "name": "Cảnh giác văn hoá \"dàn dựng giả\"",
        "deck_name": "Lo ngại về tính chân thực",
        "confidence": "Trung bình",
        "industry_leaning": False,
        "note": (
            "3 nhóm phản ứng khác nhau. Cần nói rõ 'nghi lễ thật có khách "
            "chứng kiến' trước khi vào lễ."
        ),
    },
    "P5": {
        "name": "Uy tín điểm đến (Nam Định)",
        "deck_name": "Độ thuyết phục của Nam Định",
        "confidence": "Trung bình",
        "industry_leaning": False,
        "note": (
            "Ba bản chất khác nhau: thương hiệu, địa lý, góc ngành. "
            "Mỗi bản chất cần cách giải riêng."
        ),
    },
    "P6": {
        "name": "Quá quen, không còn nhu cầu khám phá",
        "deck_name": "Thiên kiến văn hoá Việt đã quen",
        "confidence": "Tín hiệu sớm",
        "industry_leaning": False,
        "note": (
            "Hai nguồn (P05, P15), vẫn là tín hiệu sớm. Cần theo dõi ở "
            "đợt phỏng vấn tiếp theo trước khi kết luận."
        ),
    },
    "H1": {
        "name": "Khách quan tâm tín ngưỡng",
        "deck_name": "Khách quan tâm tín ngưỡng",
        "confidence": "Hypothesis",
        "industry_leaning": False,
        "note": (
            "Hứng thú thật nhưng phạm vi rộng, từ Phật giáo đến Đạo Mẫu. "
            "Không định vị bằng nhãn giới tính hoá."
        ),
    },
    "S1": {
        "name": "Tiềm năng khách nước ngoài",
        "deck_name": "Sức hút với khách nước ngoài / người tò mò văn hoá",
        "confidence": "Hypothesis",
        "industry_leaning": True,
        "note": (
            "Phỏng đoán của người Việt về nhóm vắng mặt. Cần dành suất "
            "pilot cho khách nước ngoài để kiểm chứng trực tiếp."
        ),
    },
    "S2": {
        "name": "Ẩm thực là đòn bẩy mềm",
        "deck_name": "Ẩm thực như điểm vào văn hoá",
        "confidence": "Trung bình",
        "industry_leaning": True,
        "note": (
            "Tín hiệu có thể khai thác ngay. Ẩm thực có thể là điểm vào "
            "mềm cho người chưa sẵn sàng với nội dung văn hóa nặng hơn."
        ),
    },
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
    """Lens distribution plus the locked study-level interpretation caveat."""
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
        "industry_leaning": bool(PATTERN_META[pattern_id]["industry_leaning"]),
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
        ["Kiểu phản hồi", "Số người", "Góc nhìn", "Độ tin cậy", "Điểm chính"], body
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
        '<span class="p1-leg p1-leg--diamond"></span>khách hiểu sâu</span>'
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
        f'<p class="p1-hint">Ch\u1ecdn m\u1ed9t ng\u01b0\u1eddi \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
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
        '<span class="p2-leg p2-leg--diamond"></span>khách hiểu sâu</span>'
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
        f'<p class="p2-hint">Ch\u1ecdn m\u1ed9t ng\u01b0\u1eddi \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
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
        '<span class="p3-leg p3-leg--diamond"></span>khách hiểu sâu</span>'
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
        f'<p class="p3-hint">Ch\u1ecdn m\u1ed9t ng\u01b0\u1eddi \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
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
        '<span class="h1-leg h1-leg--diamond"></span>khách hiểu sâu</span>'
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
        f'<p class="h1-hint">Ch\u1ecdn m\u1ed9t ng\u01b0\u1eddi \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
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
        '<span class="s1-leg s1-leg--diamond"></span>khách hiểu sâu</span>'
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
        f'<p class="s1-hint">Ch\u1ecdn m\u1ed9t ng\u01b0\u1eddi \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
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
        '<span class="s2-leg s2-leg--diamond"></span>khách hiểu sâu</span>'
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
        f'<p class="s2-hint">Ch\u1ecdn m\u1ed9t ng\u01b0\u1eddi \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
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
        '<span class="p5-leg p5-leg--diamond"></span>khách hiểu sâu</span>'
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
        "\u26a0\ufe0f Q060 \u0111ang ch\u1edd x\u00e1c minh b\u1ea3n ghi th\u00f4. "
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
        f'<p class="p5-hint">Ch\u1ecdn m\u1ed9t ng\u01b0\u1eddi \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
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
        '<span class="p4-leg p4-leg--diamond"></span>khách hiểu sâu</span>'
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
        f'<p class="p4-hint">Ch\u1ecdn m\u1ed9t ng\u01b0\u1eddi \u0111\u1ec3 xem tr\u00edch d\u1eabn</p>\n'
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
            r["occupation"] if pd.notna(r["occupation"]) else "",
            r["travel_spend_range"] if pd.notna(r["travel_spend_range"]) else "",
            r["acceptable_tour_price"] if pd.notna(r["acceptable_tour_price"]) else "",
        ))
    return _md_table(
        ["pid", "experience", "lens", "convert_type", "Nghề", "Spend", "mức khách chịu chi"], rows
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
            r["occupation"] if pd.notna(r["occupation"]) else "",
            spend,
            wtp_raw,
            _wtp_band(wtp_raw),
        ))
    return _md_table(
        ["pid", "Nghề", "Spend (thật)", "mức khách chịu chi (raw)", "Khoảng mức khách chịu chi"], rows
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
    return _md_table(["pid", "Dẫn chứng", "ref_id"], rows)


# ----------------------------------------------------------------- public report visuals

_VI_REPLACEMENTS = {
    "—": " / ",
    "â€”": " / ",
    "tour": "chuyến đi",
    "Tour": "Chuyến đi",
    "WTP": "mức khách chịu chi",
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


def render_data_gap(title, needed):
    """Render a clear data gap for visual fields that still need manual coding."""
    needed_text = ", ".join(_NEEDED_LABELS.get(col, col) for col in needed)
    return (
        '<div class="mach-viz mach-viz-data-gap">'
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
            f'<p>{_e(row.get("occupation", ""))}</p>'
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
        return render_data_gap("Vùng giá có thể chấp nhận", needed)
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
        return render_data_gap("Ma trận hành vi du lịch", needed)
    rows = []
    for col in needed:
        s = participants_df[col].fillna("").astype(str).str.strip().str.lower()
        rows.append((col, int(s.isin(["true", "1", "yes", "co", "có"]).sum())))
    return _md_table(["Tín hiệu", "Số người đã gắn chủ đề"], rows)


def render_interest_plot(participants_df):
    needed = ["interest_score"]
    if not _has_values(participants_df, needed):
        return render_data_gap("Điểm quan tâm đến chuyến đi", needed)
    rows = []
    for _, row in participants_df.sort_values("pid").iterrows():
        if pd.notna(row.get("interest_score")) and str(row.get("interest_score")).strip():
            rows.append((row["pid"], row.get("interest_score")))
    return _md_table(["Mã người tham gia", "Điểm quan tâm"], rows)


def render_sustainability_buckets(participants_df):
    needed = ["sustainability_awareness"]
    if not _has_values(participants_df, needed):
        return render_data_gap("Mức quen thuộc với du lịch bền vững", needed)
    counts = participants_df["sustainability_awareness"].fillna("").astype(str).str.strip()
    counts = counts[counts != ""].value_counts()
    rows = [(label, int(count)) for label, count in counts.items()]
    return _md_table(["Mức quen thuộc", "Số người đã gắn chủ đề"], rows)


def render_archetype_scatter(participants_df):
    needed = ["price_sensitivity", "cultural_depth_interest"]
    if not _has_values(participants_df, needed):
        return render_data_gap("Bản đồ nhóm khách theo giá và chiều sâu văn hoá", needed)
    rows = []
    for _, row in participants_df.sort_values("pid").iterrows():
        price = row.get("price_sensitivity", "")
        depth = row.get("cultural_depth_interest", "")
        if str(price).strip() or str(depth).strip():
            rows.append((row["pid"], price, depth))
    return _md_table(["Mã người tham gia", "Nhạy cảm với giá", "Quan tâm chiều sâu văn hoá"], rows)


# ----------------------------------------------------------------- deck report helpers

_SUSTAINABILITY_LABELS = {
    "chua_quen": "Chưa quen",
    "da_nghe_chua_ro": "Đã nghe nhưng chưa rõ",
    "hieu_ro_hon": "Hiểu rõ hơn",
}


def _deck_h(value):
    return html.escape("" if value is None else str(value), quote=True)


def _deck_num(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return str(number).replace(".", ",")


def _deck_bool_stats(participants_df, column):
    if column not in participants_df.columns:
        raise KeyError(f"Missing boolean evidence column: {column}")
    values = participants_df[column].fillna("").astype(str).str.strip().str.lower()
    true_values = {"true", "1", "yes", "co", "có"}
    false_values = {"false", "0", "no", "khong", "không"}
    valid_values = true_values | false_values | {""}
    invalid = sorted(set(values) - valid_values)
    if invalid:
        raise ValueError(f"Invalid boolean evidence values in {column}: {invalid}")
    true_count = int(values.isin(true_values).sum())
    false_count = int(values.isin(false_values).sum())
    unknown_count = int((values == "").sum())
    return {
        "true": true_count,
        "false": false_count,
        "unknown": unknown_count,
        "coded": true_count + false_count,
        "total": len(values),
    }


def _deck_bool_label(stats):
    parts = [f'{stats["true"]} có bằng chứng']
    if stats["false"]:
        parts.append(f'{stats["false"]} không')
    parts.append(f'{stats["unknown"]} chưa gắn chủ đề')
    return " · ".join(parts)


def _deck_metric(icon, value, label, detail=""):
    return (
        '<article class="deck-metric">'
        f'<span class="deck-icon"><i class="bi bi-{_deck_h(icon)}"></i></span>'
        f'<strong>{_deck_h(value)}</strong>'
        f'<span>{_deck_h(label)}</span>'
        f'<small>{_deck_h(detail)}</small>'
        '</article>'
    )


def _deck_info_pill(icon, label, value):
    return (
        '<div class="deck-info-pill">'
        f'<i class="bi bi-{_deck_h(icon)}"></i>'
        f'<span>{_deck_h(label)}</span>'
        f'<strong>{_deck_h(value)}</strong>'
        '</div>'
    )


def _deck_takeaway(text):
    return (
        '<div class="deck-takeaway">'
        '<span class="deck-takeaway-icon"><i class="bi bi-lightbulb"></i></span>'
        f'<p><strong>Chốt lại:</strong> {_deck_h(text)}</p>'
        '</div>'
    )


def _deck_note(text):
    return (
        '<div class="deck-note">'
        '<span class="deck-note-icon"><i class="bi bi-info-circle"></i></span>'
        f'<p><strong>Lưu ý:</strong> {_deck_h(text)}</p>'
        '</div>'
    )


def _deck_bar(label, count, total, icon="bar-chart-fill", value_label=None):
    total = max(int(total), 1)
    count = int(count)
    width = max(4, min(100, round(count / total * 100)))
    row_class = "deck-bar-row deck-bar-evidence" if value_label is not None else "deck-bar-row"
    return (
        f'<div class="{row_class}">'
        f'<i class="bi bi-{_deck_h(icon)}"></i>'
        f'<span>{_deck_h(label)}</span>'
        '<div class="deck-bar-track">'
        f'<div class="deck-bar-fill" style="width:{width}%"></div>'
        '</div>'
        f'<strong>{_deck_h(value_label) if value_label is not None else f"{count}/{total}"}</strong>'
        '</div>'
    )


def _deck_step(icon, title, text):
    return (
        '<article class="deck-step">'
        f'<span class="deck-icon"><i class="bi bi-{_deck_h(icon)}"></i></span>'
        f'<h4>{_deck_h(title)}</h4>'
        f'<p>{_deck_h(text)}</p>'
        '</article>'
    )


def _deck_card(icon, title, text, tone="plain"):
    return (
        f'<article class="deck-card deck-card-{_deck_h(tone)}">'
        f'<span class="deck-icon"><i class="bi bi-{_deck_h(icon)}"></i></span>'
        f'<h4>{_deck_h(title)}</h4>'
        f'<p>{_deck_h(text)}</p>'
        '</article>'
    )


def _deck_page_header(title, subtitle):
    return (
        '<div class="deck-page-header">'
        f'<h2>{_deck_h(title)}</h2>'
        f'<p>{_deck_h(subtitle)}</p>'
        '</div>'
    )


def _deck_meta_box(items):
    rows = []
    for icon, label, value in items:
        rows.append(
            '<div class="deck-meta-row">'
            f'<i class="bi bi-{_deck_h(icon)}"></i>'
            f'<strong>{_deck_h(label)}</strong>'
            f'<span>{_deck_h(value)}</span>'
            '</div>'
        )
    return '<aside class="deck-meta-box">' + "".join(rows) + '</aside>'


def _deck_page_header_meta(title, subtitle, meta_html):
    return (
        '<div class="deck-page-header deck-page-header-with-meta">'
        '<div class="deck-title-block">'
        f'<h2>{_deck_h(title)}</h2>'
        f'<p>{_deck_h(subtitle)}</p>'
        '</div>'
        f'{meta_html}'
        '</div>'
    )


def _deck_panel_html(icon, title, body, extra_class=""):
    return (
        f'<div class="deck-panel deck-visual-panel {_deck_h(extra_class)}">'
        '<div class="deck-panel-heading">'
        f'<span class="deck-icon"><i class="bi bi-{_deck_h(icon)}"></i></span>'
        f'<h3>{_deck_h(title)}</h3>'
        '</div>'
        f'{body}'
        '</div>'
    )


_DECK_QUAL_LEVELS = {
    "very_low": 18,
    "low": 28,
    "mid": 48,
    "high": 72,
    "very_high": 88,
}


def _deck_qual_width(level):
    return _DECK_QUAL_LEVELS.get(str(level), _DECK_QUAL_LEVELS["mid"])


def _deck_balance_table(rows):
    body = [
        '<div class="deck-balance-head"><span></span><span></span><strong>Hiện tại</strong><strong>Nên hướng tới</strong></div>'
    ]
    for icon, label, current, target in rows:
        body.append(
            '<div class="deck-balance-row">'
            f'<span class="deck-mini-icon"><i class="bi bi-{_deck_h(icon)}"></i></span>'
            f'<strong>{_deck_h(label)}</strong>'
            '<div class="deck-balance-track deck-balance-current">'
            f'<span style="width:{_deck_qual_width(current)}%"></span>'
            '</div>'
            '<div class="deck-balance-track deck-balance-target">'
            f'<span style="width:{_deck_qual_width(target)}%"></span>'
            '</div>'
            '</div>'
        )
    return '<div class="deck-balance-table">' + "".join(body) + '</div>'


def _deck_bottleneck_list(items):
    cards = []
    for item in items:
        idx, title, subtitle, level = item[:4]
        pids = item[4] if len(item) > 4 else None
        quote_ids = item[5] if len(item) > 5 else None
        attrs = _deck_b_interactive_attrs(pids=pids, quote_ids=quote_ids)
        cls = "deck-bottleneck" + (" b-interactive" if attrs else "")
        cards.append(
            f'<article class="{cls}"{attrs}>'
            f'<span class="deck-bottleneck-number">{_deck_h(idx)}</span>'
            '<div>'
            f'<h4>{_deck_h(title)}</h4>'
            f'<p>{_deck_h(subtitle)}</p>'
            '<div class="deck-bottleneck-track">'
            f'<span style="width:{_deck_qual_width(level)}%"></span>'
            '</div>'
            '</div>'
            '</article>'
        )
    return '<div class="deck-bottleneck-list">' + "".join(cards) + '</div>'


def _deck_signal_card(icon, title, text, tone="plain", pids=None, quote_ids=None):
    attrs = _deck_b_interactive_attrs(pids=pids, quote_ids=quote_ids)
    cls = f"deck-signal-card deck-signal-{_deck_h(tone)}" + (" b-interactive" if attrs else "")
    return (
        f'<article class="{cls}"{attrs}>'
        f'<span class="deck-mini-icon"><i class="bi bi-{_deck_h(icon)}"></i></span>'
        f'<h4>{_deck_h(title)}</h4>'
        f'<p>{_deck_h(text)}</p>'
        '</article>'
    )


def _deck_signal_grid(cards):
    return '<div class="deck-signal-grid">' + "".join(cards) + '</div>'


def _deck_action_card(icon, title, text):
    return (
        '<article class="deck-action-card">'
        f'<span class="deck-mini-icon"><i class="bi bi-{_deck_h(icon)}"></i></span>'
        f'<h4>{_deck_h(title)}</h4>'
        f'<p>{_deck_h(text)}</p>'
        '</article>'
    )


def _deck_action_flow(items):
    pieces = []
    for i, (icon, title, text) in enumerate(items):
        pieces.append(_deck_action_card(icon, title, text))
        if i < len(items) - 1:
            pieces.append('<span class="deck-flow-arrow"><i class="bi bi-chevron-right"></i></span>')
    return '<div class="deck-action-flow">' + "".join(pieces) + '</div>'


def _deck_b_interactive_attrs(pids=None, quote_ids=None):
    attrs = []
    if pids:
        pids_value = html.escape(",".join(pids), quote=True)
        attrs.append(f' data-b-pids="{pids_value}"')
    if quote_ids:
        qids_value = html.escape(",".join(quote_ids), quote=True)
        attrs.append(f' data-b-qids="{qids_value}"')
    if not attrs:
        return ""
    return (
        "".join(attrs) +
        ' role="button"'
        ' tabindex="0"'
        ' aria-expanded="false"'
    )


def _deck_b_quote_ids_from_html(body):
    quote_ids = []
    for match in re.findall(r'data-b-qids="([^"]+)"', body):
        for quote_id in match.split(","):
            quote_id = quote_id.strip()
            if quote_id and quote_id not in quote_ids:
                quote_ids.append(quote_id)
    return quote_ids


def _deck_b_quote_panel(pattern_id, quotes_df, participants_df, quote_ids=None):
    pat_quotes = quotes_df[quotes_df["pattern_id"].astype(str) == str(pattern_id)].copy()
    if quote_ids:
        qid_quotes = quotes_df[quotes_df["quote_id"].astype(str).isin(quote_ids)].copy()
        pat_quotes = pd.concat([pat_quotes, qid_quotes], ignore_index=True)
        pat_quotes = pat_quotes.drop_duplicates(subset=["quote_id"], keep="first")
    if pat_quotes.empty:
        return ""
    merged = pat_quotes.merge(
        participants_df[["pid", "lens"]], on="pid", how="left"
    )
    pids_seen = list(dict.fromkeys(merged["pid"].tolist()))
    dots = "".join(
        f'<span class="b-dot" data-pid="{_deck_h(pid)}" title="{_deck_h(pid)}">{_deck_h(pid)}</span>'
        for pid in pids_seen
    )
    _conf_labels = {"cao": "Cao", "trung_binh": "Trung bình", "som": "Tín hiệu sớm", "hypothesis": "Giả thuyết"}
    quote_items = []
    for _, row in merged.iterrows():
        text = str(row.get("quote_short") or row.get("quote_full") or "").strip()
        if not text:
            continue
        pid = str(row.get("pid", "")).strip()
        qid = str(row.get("quote_id", "")).strip()
        ctx = str(row.get("context") or "").strip()
        conf = str(row.get("confidence_level") or "").strip()
        conf_label = _conf_labels.get(conf, conf)
        conf_html = f'<span class="bqp-conf bqp-conf-{_deck_h(conf)}">{_deck_h(conf_label)}</span>' if conf_label else ""
        quote_items.append(
            f'<div class="bqp-quote" data-pid="{_deck_h(pid)}" data-qid="{_deck_h(qid)}">'
            f'<span class="bqp-pid">{_deck_h(pid)}</span>'
            f'<p class="bqp-quote-text">&#x201C;{_deck_h(text)}&#x201D;</p>'
            + (f'<p class="bqp-quote-ctx">{_deck_h(ctx)}</p>' if ctx else "")
            + conf_html
            + "</div>"
        )
    panel_id = f"bqp-{str(pattern_id).lower()}"
    return (
        f'<div class="deck-b-quote-panel" id="{_deck_h(panel_id)}" hidden>'
        '<p class="bqp-hint"><i class="bi bi-cursor-fill"></i> Bấm vào thẻ để xem bằng chứng liên quan</p>'
        f'<div class="bqp-dots">{dots}</div>'
        f'<div class="bqp-quotes">{"".join(quote_items)}</div>'
        "</div>"
    )


def _deck_b_footer(actions, takeaway):
    action_cards = "".join(_deck_action_card(icon, title, text) for icon, title, text in actions)
    return (
        '<div class="deck-b-footer">'
        f'<div class="deck-action-grid">{action_cards}</div>'
        '<div class="deck-b-takeaway">'
        '<span class="deck-b-takeaway-icon"><i class="bi bi-lightbulb-fill"></i></span>'
        f'<p><strong>Chốt lại:</strong> {_deck_h(takeaway)}</p>'
        "</div>"
        "</div>"
    )


def render_b_interactive_js():
    return (
        "<script>(function(){"
        "function resetPanel(panel){"
        "panel.hidden=true;"
        "panel.classList.remove('bqp-open');"
        "panel.querySelectorAll('.b-dot,.bqp-quote').forEach(function(x){x.classList.remove('bqp-hidden');});"
        "}"
        "function clearActive(){"
        "document.querySelectorAll('[data-b-pids],[data-b-qids]').forEach(function(x){x.classList.remove('b-active');x.setAttribute('aria-expanded','false');});"
        "document.querySelectorAll('.deck-b-quote-panel').forEach(resetPanel);"
        "}"
        "function values(el,attr){return (el.getAttribute(attr)||'').split(',').map(function(s){return s.trim();}).filter(Boolean);}"
        "function activate(el){"
        "var slide=el.closest('.deck-b-slide');"
        "if(!slide)return;"
        "var panel=slide.querySelector('.deck-b-quote-panel');"
        "if(!panel)return;"
        "var wasActive=el.classList.contains('b-active');"
        "var pids=values(el,'data-b-pids');"
        "var qids=values(el,'data-b-qids');"
        "clearActive();"
        "if(wasActive)return;"
        "el.classList.add('b-active');"
        "el.setAttribute('aria-expanded','true');"
        "panel.hidden=false;"
        "panel.classList.add('bqp-open');"
        "var visiblePids=[];"
        "panel.querySelectorAll('.bqp-quote').forEach(function(q){"
        "var pid=q.getAttribute('data-pid');"
        "var qid=q.getAttribute('data-qid');"
        "var show=(pids.length&&pids.indexOf(pid)!==-1)||(qids.length&&qids.indexOf(qid)!==-1);"
        "q.classList.toggle('bqp-hidden',!show);"
        "if(show&&visiblePids.indexOf(pid)===-1)visiblePids.push(pid);"
        "});"
        "panel.querySelectorAll('.b-dot').forEach(function(d){"
        "d.classList.toggle('bqp-hidden',visiblePids.indexOf(d.getAttribute('data-pid'))===-1);"
        "});"
        "}"
        "document.addEventListener('click',function(e){"
        "var el=e.target.closest('[data-b-pids],[data-b-qids]');"
        "if(!el){"
        "clearActive();"
        "return;"
        "}"
        "activate(el);"
        "e.stopPropagation();"
        "});"
        "document.addEventListener('keydown',function(e){"
        "var el=e.target.closest('[data-b-pids],[data-b-qids]');"
        "if(!el)return;"
        "if(e.key==='Enter'||e.key===' '){"
        "e.preventDefault();"
        "activate(el);"
        "}"
        "});"
        "})();</script>"
    )


def _deck_section_band(title, body, number=None):
    prefix = f"{number}. " if number is not None else ""
    return (
        '<div class="deck-numbered-band">'
        f'<div class="deck-band-label">{_deck_h(prefix + title)}</div>'
        f'{body}'
        '</div>'
    )


def _deck_pattern_meta_box(pattern_id, quotes_df, participants_df):
    occ = pattern_occurrence(pattern_id, quotes_df, participants_df)
    quote_count = int((quotes_df["pattern_id"] == pattern_id).sum())
    lens = pattern_lens_breakdown(pattern_id, quotes_df, participants_df)
    confidence = PATTERN_META[pattern_id]["confidence"]
    if confidence == "Hypothesis":
        confidence = "Giả thuyết"
    lens_bits = []
    if lens["customer"]:
        lens_bits.append(f'{lens["customer"]} khách')
    if lens["industry"]:
        lens_bits.append(f'{lens["industry"]} ngành')
    if lens["lead_user"]:
        lens_bits.append(f'{lens["lead_user"]} khách hiểu sâu')
    lens_note = " / ".join(lens_bits) if lens_bits else "chưa có góc nhìn"
    if lens["industry_leaning"]:
        lens_note += "; thiên góc nhìn ngành"
    return _deck_meta_box([
        ("people-fill", "Tần suất", f'{occ["count"]}/{occ["total"]} người'),
        ("chat-square-quote", "Dẫn chứng", f"{quote_count} dòng"),
        ("shield-check", "Độ tin cậy", confidence),
        ("diagram-3", "Góc nhìn", lens_note),
    ])


def _deck_b_slide(
    pattern_id,
    title,
    subtitle,
    left_icon,
    left_title,
    left_body,
    right_icon,
    right_title,
    right_body,
    actions,
    takeaway,
    quotes_df,
    participants_df,
):
    section_id = f"visual-{str(pattern_id).lower()}"
    quote_ids = _deck_b_quote_ids_from_html(left_body + right_body)
    return (
        f'<section id="{_deck_h(section_id)}" class="deck-slide deck-visual deck-b-slide">'
        + _deck_page_header_meta(title, subtitle, _deck_pattern_meta_box(pattern_id, quotes_df, participants_df))
        + '<div class="deck-b-top">'
        + _deck_panel_html(left_icon, left_title, left_body)
        + _deck_panel_html(right_icon, right_title, right_body)
        + "</div>"
        + _deck_b_footer(actions, takeaway)
        + _deck_b_quote_panel(pattern_id, quotes_df, participants_df, quote_ids)
        + "</section>"
    )


def _deck_quadrant_matrix(cards):
    return (
        '<div class="deck-quadrant-wrap">'
        '<div class="deck-axis deck-axis-top">Mức cùng gu / cùng mối quan tâm</div>'
        '<div class="deck-axis deck-axis-left">Độ thân quen</div>'
        '<div class="deck-quadrant-grid">'
        + "".join(cards)
        + '</div>'
        '</div>'
    )


def _deck_scale(label_left, label_mid, label_right, position="mid"):
    pos = {"left": 16, "mid": 50, "right": 82}.get(position, 50)
    return (
        '<div class="deck-scale">'
        '<div class="deck-scale-labels">'
        f'<span>{_deck_h(label_left)}</span><strong>{_deck_h(label_mid)}</strong><span>{_deck_h(label_right)}</span>'
        '</div>'
        '<div class="deck-scale-line">'
        f'<span class="deck-scale-point" style="left:{pos}%"></span>'
        '</div>'
        '</div>'
    )


def render_cover_stats(participants_df, quotes_df, records_df):
    n = len(participants_df)
    return (
        '<div class="deck-cover-stats">'
        + _deck_metric("people-fill", n, "Người tham gia")
        + _deck_metric("file-earmark-text", len(records_df), "Câu trích và bản ghi")
        + _deck_metric("chat-square-quote", len(quotes_df), "Bằng chứng chọn lọc")
        + _deck_metric("clipboard-data", "Định tính", "Mẫu tự nguyện, không chọn ngẫu nhiên")
        + '</div>'
        + _deck_note(
            "Đây là mẫu định tính tự nguyện, không chọn ngẫu nhiên, dùng để phát hiện tín hiệu và giả thuyết, không đại diện thị trường."
        )
    )


def render_sample_deck_visual(participants_df, quotes_df, records_df):
    n = len(participants_df)
    exp = participants_df["experience"].fillna("").astype(str).value_counts().to_dict()
    lens = participants_df["lens"].fillna("").astype(str).value_counts().to_dict()
    rows = [
        _deck_metric("people-fill", n, "Người tham gia", "chỉ dùng mã định danh"),
        _deck_metric("file-earmark-text", len(records_df), "Câu trích và bản ghi", "bản ghi tổng hợp đầy đủ"),
        _deck_metric("collection", len(quotes_df), "Bằng chứng chọn lọc", "tệp trích dẫn"),
        _deck_metric("compass", exp.get("chua_tung", 0), "Chưa / ít kinh nghiệm", "du lịch văn hoá"),
        _deck_metric("map", exp.get("da_tung", 0), "Đã có kinh nghiệm", "hoặc định hướng văn hoá"),
        _deck_metric("person-badge", lens.get("industry", 0) + lens.get("lead_user", 0), "Góc nhìn chuyên môn", "chú thích, không loại khỏi mẫu"),
    ]
    return (
        '<section class="deck-slide deck-visual">'
        + _deck_page_header("III. Thông tin dữ liệu", "Tổng quan mẫu phỏng vấn")
        + '<div class="deck-metric-grid">' + "".join(rows) + '</div>'
        + '<div class="deck-two-col">'
        '<div class="deck-panel"><h3>Nhóm kinh nghiệm</h3>'
        + _deck_bar("Chưa hoặc ít kinh nghiệm", exp.get("chua_tung", 0), n, "person-walking")
        + _deck_bar("Đã có kinh nghiệm", exp.get("da_tung", 0), n, "backpack")
        + '</div>'
        '<div class="deck-panel"><h3>Góc nhìn khi diễn giải</h3>'
        + _deck_bar("Khách tiềm năng", lens.get("customer", 0), n, "person")
        + _deck_bar("Ngành / chuyên môn", lens.get("industry", 0), n, "briefcase")
        + _deck_bar("khách hiểu sâu", lens.get("lead_user", 0), n, "star")
        + '</div></div>'
        + _deck_note("Tất cả tỷ lệ dùng mẫu số đầy đủ; góc nhìn ngành chỉ là chú thích khi diễn giải.")
        + '</section>'
    )


def _deck_wtp_band_counts(participants_df):
    df = participants_df.copy()
    mins = pd.to_numeric(df.get("wtp_min"), errors="coerce")
    maxs = pd.to_numeric(df.get("wtp_max"), errors="coerce")
    coded = df[mins.notna() | maxs.notna()].copy()
    mins = pd.to_numeric(coded.get("wtp_min"), errors="coerce")
    maxs = pd.to_numeric(coded.get("wtp_max"), errors="coerce")
    return [
        ("3-5 triệu", int(((maxs <= 5) & maxs.notna()).sum()), "Vùng thấp được chấp nhận khi chất lượng rõ"),
        ("5-8 triệu", int(((mins <= 8) & (maxs > 5) & (maxs <= 8)).sum()), "Khách nhắc tới nhiều trong phỏng vấn"),
        ("8-10 triệu", int(((maxs > 8) & (maxs <= 10)).sum()), "Có thể cân nhắc nếu dịch vụ rõ"),
        ("Chưa rõ", int(len(df) - len(coded)), "Không hỏi trực tiếp hoặc bản ghi mơ hồ"),
    ]


def render_decision_deck_visual(participants_df):
    n = len(participants_df)
    factors = [
        ("Tự do lịch trình", _deck_bool_stats(participants_df, "prefers_selftour"), "calendar-week"),
        ("Người đi cùng", _deck_bool_stats(participants_df, "companion_dependent"), "people-fill"),
        ("Cảm giác đáng tiền", _deck_bool_stats(participants_df, "price_sensitive"), "tag"),
        ("Trải nghiệm hơn nghỉ dưỡng", _deck_bool_stats(participants_df, "experience_over_resort"), "activity"),
        ("Tính chân thực", _deck_bool_stats(participants_df, "cares_about_authenticity"), "shield-check"),
    ]
    wtp_cards = []
    for idx, (label, count, detail) in enumerate(_deck_wtp_band_counts(participants_df), start=1):
        wtp_cards.append(
            '<article class="deck-price-row">'
            f'<span>{idx}</span><strong>{_deck_h(label)}</strong>'
            f'<p>{count} người - {_deck_h(detail)}</p>'
            '</article>'
        )
    return (
        '<section class="deck-slide deck-visual">'
        + _deck_page_header("IV.A. Hành vi du lịch và yếu tố ra quyết định", "Cách người tham gia chọn một chuyến đi")
        + '<div class="deck-two-col">'
        '<div class="deck-panel"><h3>Yếu tố ảnh hưởng quyết định du lịch</h3>'
        + "".join(
            _deck_bar(
                label,
                stats["true"],
                n,
                icon,
                value_label=_deck_bool_label(stats),
            )
            for label, stats, icon in factors
        )
        + '</div>'
        '<div class="deck-panel"><h3>Các khoảng giá khách nhắc tới</h3>'
        '<div class="deck-price-list">'
        + "".join(wtp_cards)
        + '</div></div></div>'
        + _deck_takeaway("Tour không cần rẻ nhất. Tour cần chứng minh rõ vì sao đáng tiền.")
        + _deck_note("Các khoảng giá chỉ dùng các dòng mức khách chịu chi (từ phỏng vấn) ghi rõ; trường hợp mơ hồ được để riêng.")
        + '</section>'
    )


def _deck_pattern_snapshot(pattern_id, quotes_df, participants_df):
    occ = pattern_occurrence(pattern_id, quotes_df, participants_df)
    quote_count = int((quotes_df["pattern_id"] == pattern_id).sum())
    lens = pattern_lens_breakdown(pattern_id, quotes_df, participants_df)
    meta = PATTERN_META[pattern_id]
    label = meta["deck_name"]
    confidence = "Giả thuyết" if meta["confidence"] == "Hypothesis" else meta["confidence"]
    lens_text = []
    if lens["customer"]:
        lens_text.append(f'{lens["customer"]} khách')
    if lens["industry"]:
        lens_text.append(f'{lens["industry"]} ngành')
    if lens["lead_user"]:
        lens_text.append(f'{lens["lead_user"]} khách hiểu sâu')
    lens_note = " / ".join(lens_text) if lens_text else "chưa có lens"
    if lens["industry_leaning"]:
        lens_note += " - thiên góc nhìn ngành"
    return (
        '<div class="deck-snapshot">'
        + _deck_info_pill("people-fill", "Tần suất", f'{occ["count"]}/{occ["total"]}')
        + _deck_info_pill("chat-square-quote", "Dẫn chứng", f"{quote_count} dòng")
        + _deck_info_pill("shield-check", "Độ tin cậy", confidence)
        + _deck_info_pill("diagram-3", "Góc nhìn", lens_note)
        + '</div>'
    )


def _deck_bind(quotes_df, participants_df):
    # Quarto calls one helper per chunk; this tiny binding avoids passing the same
    # dataframes through every nested HTML builder.
    global _deck_current_quotes, _deck_current_participants
    _deck_current_quotes = quotes_df
    _deck_current_participants = participants_df


def render_b1_visual(quotes_df, participants_df):
    left = _deck_balance_table([
        ("ear", "Nghe và quan sát", "high", "mid"),
        ("hand-index", "Chạm tay / làm trực tiếp", "low", "high"),
        ("people-fill", "Tương tác với địa phương", "low", "high"),
        ("person-walking", "Nhịp đi vừa phải", "low", "high"),
    ])
    right = _deck_bottleneck_list([
        ("1", "Thiên về nghe và quan sát", "Phần trải nghiệm chưa đủ rõ", "very_high", ["P02", "P03", "P04", "P11"]),
        ("2", "Ít hoạt động trực tiếp", "Thiếu phần chạm, làm và tham gia", "high", ["P04", "P05", "P13"], ["Q073", "Q074", "Q075", "Q076"]),
        ("3", "Nhiều kiến thức, dễ mệt", "Lịch trình có thể gây ngợp", "mid", ["P02", "P03", "P11"]),
        ("4", "Dễ giống hoạt động học tập", "Khó tạo cảm giác của một chuyến đi", "mid", ["P01", "P11"]),
    ])
    return _deck_b_slide(
        "P1",
        "IV.B.1. Trải nghiệm còn thụ động",
        "Phản ứng với mô hình tour MẠCH",
        "sliders",
        "Cán cân trải nghiệm hiện tại",
        left,
        "bar-chart-fill",
        "Điểm nghẽn chính",
        right,
        [
            ("hand-index", "Tăng hoạt động chạm tay", "Workshop, làm nghề, trải nghiệm trực tiếp"),
            ("house-heart", "Đưa khách vào đời sống địa phương", "Ăn cùng nhà dân, trò chuyện, sinh hoạt thật"),
            ("bicycle", "Tăng hoạt động di chuyển nhẹ", "Đạp xe, đi bộ, khám phá theo nhịp tự nhiên"),
            ("chat-dots", "Giảm cảm giác hàn lâm", "Ít giảng giải dài, nhiều tương tác hơn"),
        ],
        "Tour cần chuyển từ nghe về văn hoá sang trực tiếp chạm vào văn hoá.",
        quotes_df,
        participants_df,
    )


def render_b2_visual(quotes_df, participants_df):
    left = _deck_quadrant_matrix([
        _deck_signal_card("people-fill", "Người quen cùng gu", "Dễ đặt tour nhất: có bạn bè hoặc người thân cùng quan tâm.", "teal", pids=["P05", "P11"]),
        _deck_signal_card("person-lines-fill", "Người lạ cùng gu", "Có thể thử nếu nhóm nhỏ, an toàn, có nhịp làm quen.", "blue"),
        _deck_signal_card("emoji-neutral", "Người quen không cùng gu", "Cần lý do rõ hơn để rủ đi và cùng cam kết.", "amber", pids=["P04", "P10"]),
        _deck_signal_card("exclamation-triangle", "Người lạ không cùng gu", "Dễ tạo cảm giác ngại, xa lạ hoặc gượng ép.", "red"),
    ])
    right = _deck_bottleneck_list([
        ("1", "Thiếu đúng người rủ", "Hứng thú cá nhân chưa đủ để tự đặt tour", "high", ["P05", "P11"]),
        ("2", "Ngại nhóm lạ", "Tour văn hoá cần cảm giác an toàn và có người chia sẻ", "high"),
        ("3", "Gia đình / bạn bè ảnh hưởng quyết định", "Một số chuyến đi được quyết theo nhóm nhỏ", "mid", ["P04", "P10"], ["Q077", "Q078"]),
        ("4", "Có ngoại lệ", "P03/P07 thoải mái hơn với đi độc lập", "low"),
    ])
    return _deck_b_slide(
        "P2",
        "IV.B.2. Phụ thuộc vào người đi cùng",
        "Phản ứng với mô hình tour MẠCH",
        "grid-3x3-gap",
        "Ma trận người đi cùng",
        left,
        "bar-chart-fill",
        "Điểm nghẽn chính",
        right,
        [
            ("people-fill", "Thiết kế gói nhóm nhỏ", "Gói 2-4 người, gia đình nhỏ, nhóm bạn cùng mối quan tâm"),
            ("megaphone", "Truyền thông không khí tour", "Thân mật, an toàn, dễ trò chuyện và chia sẻ"),
            ("heart", "Không ép tương tác", "Tương tác vừa đủ, không tạo cảm giác bị bắt buộc"),
            ("ticket-perforated", "Mở cơ chế rủ bạn", "Ưu đãi nhóm nhỏ hoặc form đăng ký đi cùng"),
        ],
        "Tour văn hoá không chỉ bán cho một cá nhân. Nó cần tạo lý do để một nhóm nhỏ cùng muốn đi.",
        quotes_df,
        participants_df,
    )


def render_b3_visual(quotes_df, participants_df):
    left = _deck_signal_grid([
        _deck_signal_card("mortarboard", "Giống học tập / nghiên cứu", "Một số phản hồi thấy mô hình tour hơi hàn lâm.", "blue", pids=["P01", "P02", "P07", "P14"]),
        _deck_signal_card("question-circle", "Chưa rõ dành cho ai", "Người đọc khó tự nhận mình là khách phù hợp.", "plain", pids=["P03", "P05", "P08"]),
        _deck_signal_card("person-x", "Tự loại mình khỏi tour", "Có người thấy tour hợp với nhóm khác hơn.", "amber", pids=["P02", "P04", "P06", "P07"]),
        _deck_signal_card("person-check", "Tự nhận phù hợp", "Một nhóm khác lại thấy mình có thể là nhóm khách nhắm tới.", "teal", pids=["P10"]),
    ])
    right = _deck_bottleneck_list([
        ("1", "Giá trị có nhưng chưa hiện hình", "Người đọc cần thấy trải nghiệm trước khi đọc lý thuyết", "high", None, ["Q079"]),
        ("2", "Nhóm khách nhắm tới bị suy đoán theo tuổi", "Phân khúc nên dựa vào thái độ và bối cảnh đi cùng", "mid"),
        ("3", "Thông điệp dễ làm tour nặng", "Nội dung văn hoá cần được kể bằng đời sống", "high"),
        ("4", "Phản ứng trái chiều", "Tự thấy hợp và tự loại mình cùng xuất hiện", "mid"),
    ])
    return _deck_b_slide(
        "P3",
        "IV.B.3. Lệch định vị khách hàng",
        "Phản ứng với mô hình tour MẠCH",
        "signpost-split",
        "Cách mô hình tour hiện tại bị đọc",
        left,
        "bar-chart-fill",
        "Chỗ lệch định vị",
        right,
        [
            ("sparkles", "Chuyển từ học sang trải nghiệm", "Mở bằng đời sống thật, con người, ẩm thực, hoạt động"),
            ("bullseye", "Nói rõ ai sẽ thích tour", "Định vị theo thái độ và bối cảnh đi cùng"),
            ("image", "Cho thấy trải nghiệm trước chữ", "Bằng chứng hình ảnh giúp người xem tự hình dung nhanh"),
            ("chat-left-text", "Viết lại lời hứa", "Một chuyến đi có cảm xúc, không phải lớp học văn hoá"),
        ],
        "Mô hình tour cần giúp người đọc nhận ra tour này dành cho mình trong vài giây đầu.",
        quotes_df,
        participants_df,
    )


def render_b4_visual(quotes_df, participants_df):
    left = (
        _deck_scale("Quá dàn dựng", "Tổ chức có chủ đích", "Đời sống thật", "mid")
        + _deck_signal_grid([
            _deck_signal_card("mask", "Sợ bị diễn cho khách xem", "Khách nhạy với cảm giác bị sắp đặt quá mức.", "blue", pids=["P01", "P06", "P09", "P14"]),
            _deck_signal_card("person-heart", "Ưu tiên con người thật", "Đời sống và người địa phương là dấu hiệu quan trọng.", "teal", quote_ids=["Q081", "Q082", "Q083"]),
            _deck_signal_card("check-circle", "Chấp nhận có tổ chức", "Tổ chức tốt không xấu nếu không làm sai lệch văn hoá.", "plain", pids=["P07", "P08", "P11"]),
        ])
    )
    right = _deck_bottleneck_list([
        ("1", "Mất cảm giác sống", "Trải nghiệm quá sạch hoặc quá diễn sẽ bị cảnh giác", "high", None, ["Q080", "Q081", "Q083"]),
        ("2", "Không rõ đâu là thật", "Khách cần phân biệt phần đời sống với phần tổ chức cho khách", "high", None, ["Q080", "Q081", "Q083"]),
        ("3", "Người địa phương bị biến thành đạo cụ", "Cần tránh cảm giác chỉ xem một tiết mục", "mid", None, ["Q082", "Q083"]),
        ("4", "Biến tấu lệch nghĩa", "Rủi ro cao với tín ngưỡng và thực hành văn hoá", "mid", ["P07", "P08", "P11"]),
    ])
    return _deck_b_slide(
        "P4",
        "IV.B.4. Lo ngại về tính chân thực",
        "Phản ứng với mô hình tour MẠCH",
        "shield-check",
        "Phổ cảm nhận về tính thật",
        left,
        "exclamation-triangle",
        "Điểm cần tránh",
        right,
        [
            ("signpost", "Nói rõ đâu là đời sống thật", "Tách phần tự nhiên với phần tổ chức cho khách tham gia"),
            ("people", "Đặt người địa phương ở trung tâm", "Để khách gặp con người, không chỉ xem tiết mục"),
            ("shield-check", "Giữ đúng nghĩa văn hoá", "Không biến tấu làm lệch thực hành văn hoá"),
            ("camera-video", "Dùng hình ảnh hậu trường", "Cho thấy bối cảnh thật trước khi bán lời hứa"),
        ],
        "Khách không đòi trải nghiệm hoàn toàn nguyên bản. Họ cần cảm giác thật, không bị diễn quá mức.",
        quotes_df,
        participants_df,
    )


def render_b5_visual(quotes_df, participants_df):
    left = _deck_signal_grid([
        _deck_signal_card("geo-alt", "Nam Định chưa là điểm đến rõ", "Một số người chưa thấy lý do đủ mạnh để đi.", "blue", pids=["P04", "P08", "P09"]),
        _deck_signal_card("search", "Cần điểm bán chính", "Người xem cần điểm neo cụ thể để nhớ và rủ đi.", "teal", pids=["P07", "P08", "P13"]),
        _deck_signal_card("arrow-left-right", "Bị so sánh với lựa chọn khác", "Cùng ngân sách, khách cân nhắc nơi nổi tiếng hơn.", "amber", pids=["P07", "P09"]),
        _deck_signal_card("camera", "Cần bằng chứng trực quan", "Ảnh, video, khoảnh khắc cụ thể giúp dễ hình dung.", "plain", quote_ids=["Q084", "Q085", "Q086"]),
    ])
    right = _deck_bottleneck_list([
        ("1", "Thương hiệu điểm đến còn yếu", "Nam Định không tự bán được bằng tên gọi", "high"),
        ("2", "Lý do đi chưa đủ sắc", "Mô hình tour cần trả lời vì sao phải là Nam Định", "very_high"),
        ("3", "Khoảng cách / lo chuyến đi", "Với một số nhóm, vị trí làm tăng rào cản cân nhắc", "mid"),
        ("4", "Thiếu hình ảnh neo", "Khó tưởng tượng cảnh, người, món ăn, làng nghề", "high", None, ["Q084", "Q085", "Q086"]),
    ])
    return _deck_b_slide(
        "P5",
        "IV.B.5. Độ thuyết phục của Nam Định",
        "Phản ứng với mô hình tour MẠCH",
        "map",
        "Nam Định trong tâm trí khách",
        left,
        "bar-chart-fill",
        "Điểm nghẽn chính",
        right,
        [
            ("map", "Bán Nam Định trước", "Không chỉ nói tour diễn ra ở Nam Định"),
            ("stars", "Tạo khoảnh khắc đáng nhớ", "Ít nhất một lý do khiến khách thấy nơi này đáng đi"),
            ("camera-video", "Chứng minh bằng hình ảnh", "Cho thấy con người, món ăn, làng nghề, nhịp sống"),
            ("signpost", "Đặt tuyến kể rõ", "Từ cảnh quan đến người dẫn, từ món ăn đến câu chuyện"),
        ],
        "Trước khi bán tour MẠCH, cần bán được lý do vì sao Nam Định đáng đi.",
        quotes_df,
        participants_df,
    )


def render_b6_visual(quotes_df, participants_df):
    left = _deck_signal_grid([
        _deck_signal_card("house", "Văn hoá Việt bị xem là quen", "Một số người không thấy nhu cầu khám phá nội địa quá chung.", "amber", pids=["P05", "P15"]),
        _deck_signal_card("person-walking", "Tự đi được", "Nếu khác biệt không rõ, tour bị so với phương án tự túc.", "blue", pids=["P05", "P15"]),
        _deck_signal_card("binoculars", "Cần lớp khó tự tiếp cận", "Hậu trường tín ngưỡng, làng nghề, bữa ăn, người thật.", "teal", pids=["P05", "P15"]),
    ])
    right = _deck_bottleneck_list([
        ("1", "Cảm giác đã biết rồi", "Văn hoá Việt nói chung không đủ mới", "mid", ["P05", "P15"]),
        ("2", "Giá trị tour chưa khác tự túc", "Cần chứng minh phần MẠCH mở được mà khách tự đi khó có", "high", ["P05", "P15"]),
        ("3", "Dễ bị đọc là tour nội địa bình thường", "Thông điệp chung chung làm giảm lý do mua", "mid"),
        ("4", "Tín hiệu còn mỏng", "Chưa đủ để kết luận rộng, cần theo dõi đợt khách/pilot", "low"),
    ])
    return _deck_b_slide(
        "P6",
        "IV.B.6. Thiên kiến văn hoá Việt thì mình đã biết rồi",
        "Tín hiệu ban đầu",
        "door-open",
        "Khi văn hoá Việt bị xem là quen",
        left,
        "clipboard-check",
        "Phần phải chứng minh",
        right,
        [
            ("gem", "Không nói chung chung", "Tránh chỉ gọi là khám phá văn hoá Việt"),
            ("door-open", "Mở phần khách chưa biết", "Đưa khách vào lớp trải nghiệm khó tự vào"),
            ("person-heart", "Gắn với người thật", "Con người và bối cảnh tạo khác biệt với tự túc"),
            ("clipboard-check", "Đo lại trong pilot", "Theo dõi rào cản này xuất hiện ở nhóm nào"),
        ],
        "Điểm bán không phải văn hoá Việt nói chung, mà là phần khách khó tự chạm tới.",
        quotes_df,
        participants_df,
    )


def render_b7_visual(quotes_df, participants_df):
    left = _deck_signal_grid([
        _deck_signal_card("globe2", "Khách nước ngoài là nhóm vắng mặt", "Hiện mới là suy đoán từ người Việt trong mẫu.", "amber", pids=["P03", "P07", "P09", "P12"]),
        _deck_signal_card("translate", "Người học văn hoá Việt", "Có thể hấp dẫn nếu muốn hiểu sâu, không chỉ điểm danh chụp ảnh.", "blue"),
        _deck_signal_card("compass", "Người Việt tò mò văn hoá", "Cần cách kể đời thường và dễ tiếp cận hơn.", "teal", pids=["P09", "P11"]),
    ])
    right = _deck_bottleneck_list([
        ("1", "Nhu cầu chưa kiểm chứng", "Không có khách nước ngoài trong mẫu hiện tại", "very_high"),
        ("2", "Thiên góc nhìn ngành", "Một số nhận định xuất phát từ người có góc nhìn chuyên môn", "high"),
        ("3", "Thông điệp cần tách nhóm", "Khách Việt và khách nước ngoài cần lời hứa khác nhau", "mid"),
        ("4", "Cần dữ liệu trực tiếp", "Pilot phải dành slot kiểm chứng nhóm vắng mặt", "high"),
    ])
    return _deck_b_slide(
        "S1",
        "IV.B.7. Sức hút với khách nước ngoài / người tò mò văn hoá",
        "Cơ hội và giả thuyết cần kiểm chứng",
        "globe2",
        "Đọc đúng cơ hội",
        left,
        "bullseye",
        "Cần kiểm chứng",
        right,
        [
            ("signpost-split", "Tách thông điệp theo nhóm", "Không dùng một lời hứa cho tất cả"),
            ("globe2", "Dành slot pilot để kiểm chứng", "Cần dữ liệu trực tiếp từ khách nước ngoài"),
            ("chat-left-text", "Viết bản kể dễ hiểu", "Bản cho khách Việt bắt đầu từ đời sống và con người"),
            ("clipboard-data", "Theo dõi sau trải nghiệm", "Đo hiểu, thích, sẵn sàng trả tiền và giới thiệu"),
        ],
        "Khách nước ngoài là cơ hội đáng kiểm chứng, chưa phải kết luận nhu cầu.",
        quotes_df,
        participants_df,
    )


def render_b8_visual(quotes_df, participants_df):
    left = _deck_signal_grid([
        _deck_signal_card("egg-fried", "Ẩm thực là cửa vào mềm", "Dễ tiếp cận hơn nội dung văn hoá nặng kiến thức.", "teal", pids=["P03", "P07", "P10", "P11", "P14"], quote_ids=["Q087", "Q089"]),
        _deck_signal_card("house-heart", "Bữa ăn tại nhà dân", "Có thể kéo khách vào đời sống địa phương.", "blue", pids=["P12", "P14"], quote_ids=["Q087"]),
        _deck_signal_card("chat-dots", "Câu chuyện sau món ăn", "Món ăn cần đi cùng người nấu, bối cảnh và ký ức.", "plain", quote_ids=["Q087", "Q088"]),
    ])
    right = _deck_bottleneck_list([
        ("1", "Nếu chỉ lo cho khách ăn", "Ẩm thực mất vai trò mở cửa vào văn hoá", "high", None, ["Q087", "Q088", "Q089"]),
        ("2", "Nếu tách khỏi người nấu", "Thiếu lớp con người và đời sống phía sau món ăn", "mid", None, ["Q087", "Q088"]),
        ("3", "Nếu trình bày quá nặng", "Câu chuyện món ăn cần mềm, gần, dễ nghe", "mid", None, ["Q088"]),
        ("4", "Nếu thiếu điểm nhấn hình ảnh", "Người xem khó hình dung tour hấp dẫn ra sao", "high", None, ["Q089"]),
    ])
    return _deck_b_slide(
        "S2",
        "IV.B.8. Ẩm thực như điểm vào văn hoá",
        "Cơ hội có thể tận dụng ngay",
        "egg-fried",
        "Ẩm thực như cửa vào",
        left,
        "signpost",
        "Những bẫy cần tránh",
        right,
        [
            ("utensils", "Đưa ẩm thực thành điểm nhấn", "Không để nó chỉ lo cho khách ăn"),
            ("person-heart", "Gắn với người địa phương", "Ai nấu, ăn ở đâu, câu chuyện nào phía sau"),
            ("camera", "Dùng làm điểm nhấn hình ảnh", "Hình ảnh món ăn làm tour mềm và dễ hình dung"),
            ("house-heart", "Nối với đời sống", "Từ món ăn mở sang nhà dân, làng nghề, ký ức địa phương"),
        ],
        "Ẩm thực có thể làm phần văn hoá sâu trở nên mềm hơn, đời thường hơn và dễ bước vào hơn.",
        quotes_df,
        participants_df,
    )


def render_b9_visual(quotes_df, participants_df):
    left = _deck_signal_grid([
        _deck_signal_card("flower1", "Quan tâm tín ngưỡng là phạm vi rộng", "Từ Phật giáo, Đạo Mẫu đến các thực hành văn hoá khác.", "amber", pids=["P01", "P05", "P11", "P14"]),
        _deck_signal_card("shield-check", "Cần vùng an toàn", "Chủ đề tín ngưỡng dễ tạo phòng bị nếu kể quá bí ẩn.", "blue", quote_ids=["Q090"]),
        _deck_signal_card("person-badge", "Cần người dẫn đủ tin cậy", "Người dẫn giúp khách hiểu, hỏi và tiếp nhận theo nhịp của mình.", "teal", pids=["P05", "P11", "P14"]),
    ])
    right = _deck_bottleneck_list([
        ("1", "Không phải thị hiếu đại trà", "Mức quan tâm không trải đều ở mọi nhóm khách", "mid"),
        ("2", "Không chỉ là Đạo Mẫu", "Quan tâm tín ngưỡng rộng hơn một nghi lễ cụ thể", "high"),
        ("3", "Không giới tính hoá", "Tránh mọi nhãn giới tính hoá", "very_high"),
        ("4", "Cần kể bằng đời sống", "Nếu quá bí ẩn hoặc học thuật, khách dễ phòng bị", "mid", None, ["Q090"]),
    ])
    return _deck_b_slide(
        "H1",
        "IV.B.9. Sự quan tâm đến yếu tố tín ngưỡng",
        "Tín hiệu ban đầu",
        "flower1",
        "Vùng quan tâm tín ngưỡng",
        left,
        "exclamation-triangle",
        "Vùng rủi ro truyền thông",
        right,
        [
            ("layers", "Đặt tín ngưỡng là lớp chiều sâu", "Không biến thành thông điệp chính cho toàn thị trường"),
            ("chat-heart", "Kể bằng ngôn ngữ dễ hiểu", "Gắn với con người, đời sống và câu chuyện địa phương"),
            ("person-badge", "Dùng người dẫn tin cậy", "Cho phép hỏi, hiểu và tiếp nhận theo nhịp của khách"),
            ("clipboard-data", "Đo phản ứng trong pilot", "Theo dõi ai thật sự hứng thú sau trải nghiệm"),
        ],
        "Tín ngưỡng nên là lớp trải nghiệm sâu cho nhóm phù hợp, không phải nhãn bán hàng đại trà.",
        quotes_df,
        participants_df,
    )


def _deck_awareness_card(icon, title, bullets, footer, count=None, total=None):
    count_html = ""
    if count is not None and total is not None:
        count_html = f'<span class="deck-count-badge">{int(count)}/{int(total)}</span>'
    return (
        '<article class="deck-awareness-card">'
        '<div class="deck-awareness-title">'
        f'<span class="deck-mini-icon"><i class="bi bi-{_deck_h(icon)}"></i></span>'
        f'<h4>{_deck_h(title)}</h4>'
        f'{count_html}'
        '</div>'
        '<ul>'
        + "".join(f'<li>{_deck_h(b)}</li>' for b in bullets)
        + '</ul>'
        f'<p class="deck-card-footer">{_deck_h(footer)}</p>'
        '</article>'
    )


def _deck_term_card(label, text):
    return (
        '<article class="deck-term-card">'
        f'<strong>{_deck_h(label)}</strong>'
        f'<p>{_deck_h(text)}</p>'
        '</article>'
    )


def _deck_show_cell(icon, label):
    return (
        '<article class="deck-show-cell">'
        f'<span class="deck-mini-icon"><i class="bi bi-{_deck_h(icon)}"></i></span>'
        f'<strong>{_deck_h(label)}</strong>'
        '</article>'
    )


def _deck_implication_card(icon, title, text, tone="plain"):
    return (
        f'<article class="deck-implication-card deck-implication-{_deck_h(tone)}">'
        f'<span class="deck-mini-icon"><i class="bi bi-{_deck_h(icon)}"></i></span>'
        f'<h4>{_deck_h(title)}</h4>'
        f'<p>{_deck_h(text)}</p>'
        '</article>'
    )


def render_sustainability_deck_visual(participants_df):
    counts_raw = participants_df["sustainability_awareness"].fillna("").astype(str).str.strip()
    counts = counts_raw[counts_raw != ""].value_counts().to_dict()
    total_coded = sum(counts.values())
    coded_base = max(total_coded, 1)
    familiarity = (
        '<div class="deck-familiarity-flow">'
        + _deck_awareness_card(
            "question-circle",
            "Chưa quen",
            ["Chưa từng nghe", "Hoặc chỉ đoán là môi trường"],
            "Không nên dùng thuật ngữ quá sớm",
            counts.get("chua_quen", 0),
            coded_base,
        )
        + '<span class="deck-flow-arrow"><i class="bi bi-chevron-right"></i></span>'
        + _deck_awareness_card(
            "ear",
            "Đã nghe nhưng chưa rõ",
            ["Biết qua báo chí / internet", "Nhưng còn khá lý thuyết"],
            "Cần giải thích bằng ví dụ cụ thể",
            counts.get("da_nghe_chua_ro", 0),
            coded_base,
        )
        + '<span class="deck-flow-arrow"><i class="bi bi-chevron-right"></i></span>'
        + _deck_awareness_card(
            "lightbulb",
            "Hiểu rõ hơn",
            ["Liên hệ với cộng đồng", "Bảo tồn văn hoá, môi trường", "Giá trị quay lại cộng đồng"],
            "Có thể dùng như lớp ý nghĩa sâu hơn",
            counts.get("hieu_ro_hon", 0),
            coded_base,
        )
        + '</div>'
    )
    b2c_bridge = (
        '<div class="deck-sustain-bridge">'
        + _deck_term_card("Không nên bắt đầu bằng", "“Du lịch bền vững”")
        + '<span class="deck-flow-arrow"><i class="bi bi-chevron-right"></i></span>'
        + '<div class="deck-show-panel"><h4>Nên cho khách thấy</h4><div class="deck-show-grid">'
        + _deck_show_cell("people-fill", "Gặp người địa phương")
        + _deck_show_cell("house-heart", "Ăn cùng nhà dân")
        + _deck_show_cell("journal-text", "Hiểu câu chuyện làng nghề")
        + _deck_show_cell("heart", "Tôn trọng đời sống thật")
        + _deck_show_cell("recycle", "Giá trị quay lại cộng đồng")
        + '</div></div></div>'
    )
    implications = (
        '<div class="deck-implication-grid">'
        + _deck_implication_card("person-fill", "Với khách mua lẻ", "Bền vững là lớp ý nghĩa phía sau trải nghiệm.", "teal")
        + _deck_implication_card("briefcase", "Với đối tác tổ chức", "Có thể dùng thuật ngữ trực tiếp hơn nếu họ quen ngôn ngữ phát triển cộng đồng.", "blue")
        + _deck_implication_card("bullseye", "Pilot", "Đo xem khách có hiểu rõ hơn sau trải nghiệm hay không.", "amber")
        + '</div>'
    )
    return (
        '<section id="visual-sustainability" class="deck-slide deck-visual deck-sustainability-slide">'
        + _deck_page_header_meta(
            "IV.C. Mức độ quen thuộc với du lịch bền vững",
            "Hiểu về khái niệm trong nhóm phỏng vấn",
            _deck_meta_box([
                ("people-fill", "Mẫu", f"N={len(participants_df)}"),
                ("clipboard-data", "Đã gắn chủ đề", f"{total_coded}/{len(participants_df)} người"),
                ("info-circle", "Lưu ý", "mẫu có chủ đích, không đại diện thị trường"),
            ]),
        )
        + _deck_section_band("Mức độ quen thuộc", familiarity, 1)
        + _deck_section_band("Cách nói dễ hiểu hơn với khách mua lẻ", b2c_bridge, 2)
        + _deck_section_band("Hàm ý sử dụng", implications, 3)
        + _deck_takeaway("Bền vững nên là nguyên tắc thiết kế và lớp ý nghĩa sau trải nghiệm, không phải thuật ngữ đầu tiên để bán tour.")
        + '</section>'
    )


def _deck_archetype_card(icon, title, rows, tone="plain"):
    return (
        f'<article class="deck-archetype-card-rich deck-archetype-{_deck_h(tone)}">'
        '<div class="deck-archetype-card-head">'
        f'<span class="deck-icon"><i class="bi bi-{_deck_h(icon)}"></i></span>'
        f'<h4>{_deck_h(title)}</h4>'
        '</div>'
        '<div class="deck-archetype-rows">'
        + "".join(
            '<div class="deck-archetype-row">'
            f'<strong>{_deck_h(label)}</strong>'
            f'<span>{_deck_h(text)}</span>'
            '</div>'
            for label, text in rows
        )
        + '</div>'
        '</article>'
    )


def render_archetype_deck_visual(participants_df):
    n = len(participants_df)
    companion = _deck_bool_stats(participants_df, "companion_dependent")
    selftour = _deck_bool_stats(participants_df, "prefers_selftour")
    authenticity = _deck_bool_stats(participants_df, "cares_about_authenticity")
    sustainability_values = participants_df["sustainability_awareness"].fillna("").astype(str).str.strip()
    sustainability = int((participants_df["sustainability_awareness"].fillna("") == "hieu_ro_hon").sum())
    sustainability_coded = int((sustainability_values != "").sum())
    sustainability_unknown = n - sustainability_coded
    signal_strip = (
        '<div class="deck-archetype-signal-strip">'
        + _deck_info_pill("people-fill", "Phụ thuộc người đi cùng", _deck_bool_label(companion))
        + _deck_info_pill("person-walking", "Tự tổ chức / tự khám phá", _deck_bool_label(selftour))
        + _deck_info_pill("shield-check", "Quan tâm tính thật", _deck_bool_label(authenticity))
        + _deck_info_pill(
            "leaf",
            "Hiểu rõ hơn về bền vững",
            f"{sustainability}/{sustainability_coded} đã gắn chủ đề · {sustainability_unknown} chưa gắn chủ đề",
        )
        + '</div>'
    )
    cards = [
        _deck_archetype_card(
            "people-fill",
            "1. Gia đình / ưu tiên yên tâm",
            [
                ("Dấu hiệu", "Cần an toàn, lịch trình nhẹ, dịch vụ rõ và người dẫn đáng tin."),
                ("MẠCH nên nhấn", "Đi cùng người thân, tiện nghi đủ tốt, cảm giác đáng tiền."),
                ("Rào cản", "Nếu lịch trình quá nặng kiến thức hoặc thiếu nghỉ ngơi."),
            ],
            "blue",
        ),
        _deck_archetype_card(
            "chat-dots",
            "2. Tò mò văn hoá nhưng cần bạn đồng hành",
            [
                ("Dấu hiệu", "Có hứng thú, nhưng khó tự đặt tour nếu đi một mình hoặc nhóm lạ."),
                ("MẠCH nên nhấn", "Nhóm nhỏ thân mật, dễ rủ bạn, không khí dễ trò chuyện."),
                ("Rào cản", "Ngại gượng ép, ngại không cùng gu, thiếu người chia sẻ."),
            ],
            "teal",
        ),
        _deck_archetype_card(
            "backpack",
            "3. Tự khám phá / thích đời sống thật",
            [
                ("Dấu hiệu", "Thích tự do, ghét tour đóng khung, nhạy với cảm giác dàn dựng."),
                ("MẠCH nên nhấn", "Phần khó tự tiếp cận: người thật, hậu trường, nhịp sống địa phương."),
                ("Rào cản", "Nếu tour không khác rõ với tự đi hoặc quá bị quản lý."),
            ],
            "plain",
        ),
        _deck_archetype_card(
            "heart",
            "4. Chiều sâu văn hoá / cộng đồng",
            [
                ("Dấu hiệu", "Quan tâm câu chuyện con người, làng nghề, tín ngưỡng, cộng đồng."),
                ("MẠCH nên nhấn", "Ý nghĩa phía sau trải nghiệm và vai trò của người địa phương."),
                ("Rào cản", "Nếu kể quá học thuật hoặc dùng thuật ngữ bền vững quá sớm."),
            ],
            "teal",
        ),
    ]
    bottom = (
        '<div class="deck-archetype-bottom">'
        + _deck_archetype_card(
            "globe2",
            "Nhóm cần kiểm chứng riêng trong pilot",
            [
                ("Giả thuyết", "Khách nước ngoài / người tò mò văn hoá Việt có thể hấp dẫn."),
                ("Cần đo", "Hiểu đúng giá trị, sẵn sàng trả tiền, khả năng giới thiệu lại."),
                ("Lưu ý", "Hiện chưa có dữ liệu trực tiếp từ khách nước ngoài."),
            ],
            "amber",
        )
        + _deck_archetype_card(
            "person-badge",
            "Góc nhìn chuyên môn / ngành",
            [
                ("Vai trò", "Nguồn kiểm tra sản phẩm, đối tác triển khai, góc kiểm tra chất lượng."),
                ("Không nên dùng", "Không biến thành chân dung khách hàng chính."),
                ("Giá trị", "Giúp soi vận hành, tính chân thực và mức sẵn sàng của đối tác."),
            ],
            "plain",
        )
        + '</div>'
    )
    return (
        '<section id="visual-archetypes" class="deck-slide deck-visual deck-archetype-slide">'
        + _deck_page_header_meta(
            "IV.D. Nhóm khách hàng mục tiêu",
            "Kiểu khách tạm thời từ dữ liệu phỏng vấn",
            _deck_meta_box([
                ("people-fill", "Mẫu", f"N={n}"),
                ("clipboard-data", "Loại dữ liệu", "phỏng vấn định tính"),
                ("info-circle", "Lưu ý", "không ép thành chân dung khách hàng duy nhất"),
            ]),
        )
        + _deck_section_band("Tín hiệu nền để đọc kiểu khách", signal_strip)
        + '<div class="deck-archetype-board">' + "".join(cards) + '</div>'
        + bottom
        + _deck_takeaway("MẠCH chưa cần chốt một chân dung khách hàng duy nhất. Pilot nên kiểm chứng nhóm nào vừa thích tour, vừa sẵn sàng trả tiền, vừa muốn giới thiệu lại.")
        + '</section>'
    )


def render_concept_advantage_visual(participants_df, quotes_df):
    return (
        '<section class="deck-slide deck-visual">'
        + _deck_page_header("V.1. Những điểm mô hình tour đang có lợi thế", "Kết luận từ nghiên cứu trước pilot")
        + '<div class="deck-card-grid">'
        + _deck_card("people", "Gặp người", "Mô hình tour có cơ hội chạm vào nhu cầu hiểu con người và đời sống địa phương.", "teal")
        + _deck_card("bicycle", "Hoạt động địa phương", "Các hoạt động trực tiếp giúp tour khác với việc đọc hoặc nghe kiến thức.", "blue")
        + _deck_card("egg-fried", "Ẩm thực", "Ẩm thực là điểm vào mềm để kéo khách đến gần văn hoá.", "teal")
        + _deck_card("gem", "Làng nghề", "Làng nghề và sinh hoạt thật có thể tạo lý do khác biệt.", "plain")
        + _deck_card("building", "Tín ngưỡng", "Tín ngưỡng là lớp chiều sâu nếu kể an toàn và dễ hiểu.", "amber")
        + _deck_card("house-heart", "Cộng đồng", "Vai trò địa phương giúp mô hình tour có ý nghĩa hơn tour đại trà.", "teal")
        + '</div>'
        + '<div class="deck-flow">'
        + _deck_step("hand-index", "Trực tiếp chạm tay", "Tăng phần làm, ăn, gặp và di chuyển nhẹ.")
        + _deck_step("map", "Làm rõ Nam Định đáng đi", "Cần điểm neo cụ thể về người, nơi và khoảnh khắc.")
        + _deck_step("people-fill", "Thiết kế cho nhóm nhỏ", "Bán trải nghiệm đi cùng bạn bè, người thân hoặc người cùng gu.")
        + '</div>'
        + _deck_takeaway("Lợi thế của MẠCH là chiều sâu; điều cần làm là chuyển chiều sâu thành trải nghiệm cụ thể, dễ hiểu và đáng tiền.")
        + '</section>'
    )


def render_limitations_visual(participants_df):
    return (
        '<section class="deck-slide deck-visual">'
        + _deck_page_header("V.2. Giới hạn của nghiên cứu", "Điều cần nhớ khi đọc kết quả nghiên cứu")
        + '<div class="deck-card-grid">'
        + _deck_card("pie-chart", "Không đại diện thị trường", f"{len(participants_df)} phỏng vấn định tính, dùng để phát hiện tín hiệu.", "blue")
        + _deck_card("people", "Mẫu có chủ đích", "Một số người có nền tảng liên quan đến văn hoá, cộng đồng hoặc du lịch.", "plain")
        + _deck_card("globe2", "Chưa có dữ liệu trực tiếp từ khách nước ngoài", "Nhận định S1 vẫn là giả thuyết cần kiểm chứng.", "amber")
        + _deck_card("bar-chart", "Một số tín hiệu còn mỏng", "P6 và vài điểm hành vi cần theo dõi thêm.", "plain")
        + _deck_card("cart-check", "Chưa đo hành vi mua thật", "Hiện mới là phản ứng với mô hình tour, chưa phải đặt tour thật.", "teal")
        + '</div>'
        + _deck_takeaway("Báo cáo này giúp MẠCH biết điều gì đáng theo đuổi. Pilot mới là bước kiểm chứng nhu cầu thật, mức sẵn sàng trả tiền và khả năng giới thiệu lại.")
        + _deck_note("Khi đưa ra ngoài MẠCH, cần ẩn danh lại và kiểm tra đồng thuận/pháp lý.")
        + '</section>'
    )


def _pilot_funnel_card(number, label, question, pilot_question, measure):
    return (
        '<article class="pilot-funnel-card">'
        '<div class="pilot-funnel-head">'
        f'<span class="pilot-step-number">{_deck_h(number)}</span>'
        f'<span class="pilot-step-label">{_deck_h(label)}</span>'
        '</div>'
        f'<h3>{_deck_h(question)}</h3>'
        '<div class="pilot-question">'
        '<strong>Câu hỏi pilot</strong>'
        f'<p>{_deck_h(pilot_question)}</p>'
        '</div>'
        f'<p class="pilot-measure"><strong>Đo bằng:</strong> {_deck_h(measure)}</p>'
        '</article>'
    )


def _pilot_signal_item(number, title, text):
    return (
        '<article class="pilot-signal-item">'
        f'<span class="pilot-signal-number">{_deck_h(number)}</span>'
        '<div>'
        f'<h4>{_deck_h(title)}</h4>'
        f'<p>{_deck_h(text)}</p>'
        '</div>'
        '</article>'
    )


def render_pilot_test_visual():
    funnel_cards = [
        ("01", "Nhu cầu", "Có muốn đi không?", "Ai đăng ký khi lời mời tour đủ rõ?", "Đăng ký, lý do huỷ, người đi cùng"),
        ("02", "Thông điệp", "Có hiểu đúng giá trị MẠCH không?", "Khách hiểu tour theo cách nào?", "Thông điệp nhớ được, điểm hấp dẫn"),
        ("03", "Trải nghiệm", "Trải nghiệm có chạm không?", "Khoảnh khắc nào khiến khách thấy mình đang ở trong đời sống văn hoá?", "Khoảnh khắc nhớ nhất, mức tham gia"),
        ("04", "Giá trị", "Có thấy đáng tiền không?", "Phần nào tạo giá trị so với mức giá?", "Mức sẵn sàng trả tiền, so sánh lựa chọn khác"),
        ("05", "Lan toả", "Có kể lại hoặc quay lại không?", "Sau 2-4 tuần, khách còn nhớ và kể lại điều gì?", "Giới thiệu, mua lại, câu chuyện kể lại"),
    ]
    signal_items = [
        ("1", "Trước tour", "Kỳ vọng, lý do đăng ký, người đi cùng"),
        ("2", "Trong tour", "Quan sát tham gia, câu hỏi, điểm nghẽn"),
        ("3", "Ngay sau tour", "Phản ứng đầu, cảm nhận, ý định giới thiệu"),
        ("4", "Sau 2-4 tuần", "Ký ức còn lại, câu chuyện kể lại, mua lại"),
    ]
    funnel_parts = []
    for idx, card in enumerate(funnel_cards):
        funnel_parts.append(_pilot_funnel_card(*card))
        if idx < len(funnel_cards) - 1:
            funnel_parts.append('<span class="pilot-funnel-arrow" aria-hidden="true"><i class="bi bi-arrow-right"></i></span>')

    signal_parts = []
    for idx, item in enumerate(signal_items):
        signal_parts.append(_pilot_signal_item(*item))
        if idx < len(signal_items) - 1:
            signal_parts.append('<span class="pilot-timeline-arrow" aria-hidden="true"><i class="bi bi-arrow-right"></i></span>')

    return (
        '<section id="pilot-readiness" class="deck-slide deck-visual pilot-readiness-visual">'
        '<div class="pilot-readiness-header">'
        '<p class="pilot-readiness-kicker">KẾT LUẬN PILOT TOUR</p>'
        '<h2>Pilot cần chứng minh 5 điều trước khi nhân rộng</h2>'
        '<p>Không chỉ kiểm tra vận hành, pilot phải xác nhận nhu cầu thật, trải nghiệm thật và khả năng giới thiệu lại tour.</p>'
        '</div>'
        '<div class="pilot-readiness-panel">'
        '<div class="pilot-section-copy">'
        '<h3>5 câu hỏi quyết định</h3>'
        '<p>Nếu một câu trả lời còn yếu, không nên nhân rộng ngay, cần chỉnh sản phẩm, thông điệp hoặc dịch vụ trước.</p>'
        '</div>'
        f'<div class="pilot-funnel">{"".join(funnel_parts)}</div>'
        '</div>'
        '<div class="pilot-signal-panel">'
        '<div class="pilot-section-copy">'
        '<h3>4 thời điểm thu thập tín hiệu</h3>'
        '<p>Dùng cùng một bộ câu hỏi ngắn để thấy khách thay đổi kỳ vọng, cảm nhận và ký ức sau tour.</p>'
        '</div>'
        f'<div class="pilot-signal-timeline">{"".join(signal_parts)}</div>'
        '</div>'
        '<div class="pilot-decision-rule">'
        '<span><i class="bi bi-exclamation-circle-fill"></i></span>'
        '<p><strong>Quy tắc quyết định:</strong> Nếu pilot chỉ chạy mượt nhưng khách không hiểu, không thấy đáng tiền và không kể lại được, tour chưa sẵn sàng nhân rộng.</p>'
        '</div>'
        + _deck_note("Đây là khung đo cho pilot sắp tới, không phải kết quả đã thu thập.")
        + '</section>'
    )
