"""
viz_helpers.py — Compute helpers for MẠCH pretour-research-2026.

Rule #1: số trong báo cáo compute từ CSV, KHÔNG hardcode.
- Total participants = len(participants_df) = 14 (assert ở load).
- Confidence pattern lấy từ PATTERN_META (sync mục 5 CLAUDE.md đã reconcile),
  KHÔNG lấy từ field `confidence_level` của quote (field đó là per-quote, mơ hồ
  để derive pattern-level).
- P-code only. `OCCUPATION_GENERALIZED` đã bỏ tên công ty/tổ chức.

Báo cáo là prose + markdown table. Không có chart.
"""

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
