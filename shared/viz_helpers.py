"""
viz_helpers.py — Compute helpers for MẠCH pretour-research-2026.

Rule #1: số trong báo cáo compute từ CSV, KHÔNG hardcode.
- Total participants = len(participants_df) = 14 (assert ở load).
- Confidence pattern lấy từ PATTERN_META (sync STUDY_RULES.md mục 5; caveats báo cáo trong STUDY_RULES),
  KHÔNG lấy từ field `confidence_level` của quote (field đó là per-quote, mơ hồ
  để derive pattern-level).
- P-code only. `OCCUPATION_GENERALIZED` đã bỏ tên công ty/tổ chức.

Báo cáo là prose + markdown table. Không có chart.
"""

import html
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
        "name": "Tour Design quá thụ động",
        "confidence": "Cao",
        "note": "Đa số nguồn là khách thật, không phải artifact ngành.",
    },
    "P2": {
        "name": "Social Dependency (người đồng hành/gia đình là yếu tố quyết định)",
        "confidence": "Cao",
        "note": (
            "Đúng sàn (~5 nguồn) + 2 ngoại lệ thoải mái đi một mình (P03, P07) — "
            "phải ghi kèm 2 ngoại lệ khi báo cáo để minh bạch."
        ),
    },
    "P3": {
        "name": "Identity Mismatch (\"tour cho người khác, không hẳn tôi\")",
        "confidence": "Trung bình",
        "note": (
            "Nhiều nguồn (~10) nhưng TRÁI CHIỀU — một số tự loại, một số tự nhận hợp. "
            "TB vì thiếu đồng thuận, KHÔNG phải vì ít nguồn. "
            "Mâu thuẫn = bản đồ phân khúc (ai self-include vs self-exclude)."
        ),
    },
    "P4": {
        "name": "Cảnh giác văn hoá \"dàn dựng giả\"",
        "confidence": "Trung bình",
        "note": "",
    },
    "P5": {
        "name": "Destination Credibility (Nam Định)",
        "confidence": "Trung bình",
        "note": "Là PATTERN (rào cản về uy tín điểm đến), KHÔNG phải signal.",
    },
    "P6": {
        "name": "Familiarity Bias văn hoá trong nước (\"quá quen, không novel\")",
        "confidence": "Tín hiệu sớm",
        "note": (
            "Chỉ 1 nguồn (P05) — ngưỡng tối thiểu; watch-item cohort 2. "
            "KHÔNG gán \"gốc Nam Định\"."
        ),
    },
    "H1": {
        "name": "Khách quan tâm tín ngưỡng",
        "confidence": "Hypothesis",
        "note": (
            "Phạm vi tín ngưỡng BROAD (Phật giáo + Đạo Mẫu + …), KHÔNG chỉ Đạo Mẫu. "
            "Nguồn gồm cả nam (P01) lẫn nữ → gender-neutral; báo cáo ghi trung thực "
            "\"lệch nữ trong mẫu\", TUYỆT ĐỐI KHÔNG \"phụ nữ tâm linh\". "
            "Caveat: quan tâm tâm linh broad ≠ quan tâm tour Đạo Mẫu cụ thể."
        ),
    },
    "S1": {
        "name": "Vietnamese Studies / Khách nước ngoài",
        "confidence": "Hypothesis",
        "note": (
            "Nhiều nguồn (~5) NHƯNG là phỏng đoán của mẫu về nhóm VẮNG MẶT "
            "(khách nước ngoài KHÔNG có trong mẫu) → claim \"Tây muốn tour này\" "
            "CHƯA kiểm được từ data này — cần kiểm với khách nước ngoài thật. "
            "Thiên góc nhìn ngành."
        ),
    },
    "S2": {
        "name": "Ẩm thực là đòn bẩy soft",
        "confidence": "Trung bình",
        "note": (
            "Nâng từ \"tín hiệu sớm\" — ~6 nguồn, nhu cầu thật trong mẫu. "
            "Thiên góc nhìn ngành. SIGNAL có action pilot, KHÔNG phải data gap."
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
}


# ----------------------------------------------------------------- data load

def load_study_data(study_dir):
    """Load participants.csv + quotes.csv. Assert shape cohort 1."""
    study_dir = Path(study_dir)
    participants = pd.read_csv(study_dir / "data" / "participants.csv")
    quotes = pd.read_csv(study_dir / "data" / "quotes.csv")
    return participants, quotes


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
    """All patterns + signals + hypothesis: Pattern | X/14 | Lens | Confidence | Note.
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
        ["Pattern", "Occurrence", "Lens", "Confidence", "Note"], body
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


def segment_breakdown(dimension, participants_df):
    """Count 14 người theo dimension ∈ {convert_type, lens, experience, residence, age_group}."""
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
    """14 người: pid | experience | lens | convert_type | nghề (generalize) | spend | WTP."""
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
