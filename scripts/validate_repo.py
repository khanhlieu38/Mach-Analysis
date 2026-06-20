#!/usr/bin/env python3
"""Repository data, privacy, metadata, and interaction smoke checks."""

from __future__ import annotations

import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "studies" / "pretour-research-2026"
DATA = STUDY / "data"
sys.path.insert(0, str(ROOT / "shared"))

import viz_helpers as viz  # noqa: E402


PARTICIPANT_COLUMNS = [
    "pid", "experience", "lens", "age_group", "residence", "occupation",
    "convert_type", "convert_condition", "decision_style", "travel_spend_range",
    "acceptable_tour_price", "note", "wtp_min", "wtp_max", "interest_score",
    "prefers_selftour", "companion_dependent", "price_sensitive",
    "experience_over_resort", "cares_about_authenticity",
    "sustainability_awareness", "price_sensitivity", "cultural_depth_interest",
]
QUOTE_COLUMNS = [
    "quote_id", "pid", "pattern_id", "theme", "subtheme", "quote_full",
    "quote_short", "context", "confidence_level", "ref_id",
]
RECORD_COLUMNS = [
    "record_id", "pdf_entry_id", "pid", "record_type", "theme", "subtheme",
    "record_text", "record_short", "source_status", "context", "ref_id",
]
TRACKER_COLUMNS = [
    "finding_id", "cohort", "status", "evidence_delta", "confidence_after",
    "date", "note",
]
ALLOWED_OCCUPATIONS = {
    "Chức danh không nêu", "Trợ lý giám đốc", "Giảng viên đại học",
    "Kinh doanh tự do", "Nhân viên văn phòng", "Nhân viên ngành xuất khẩu",
    "Ngành thời trang (cựu ngành du lịch)", "Nhân sự ngành tài chính",
    "Sales xuất khẩu", "Quản lý doanh nghiệp (cựu ngành xuất khẩu)",
    "Phát triển cộng đồng", "Nghỉ hưu",
    "Giảng viên đại học (cựu ngành du lịch)", "Ngành du lịch cộng đồng",
    "Du học sinh",
}
CONFIDENCE_TO_CSV = {
    "Cao": "cao",
    "Trung bình": "trung_binh",
    "Tín hiệu sớm": "som",
    "Hypothesis": "hypothesis",
}
REF_RE = re.compile(r"^[A-Z]_P\d{2}_\d{4}Q[1-4]_(?:p\d+|t\d+|r\d+)$")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?84|0)\s*\d(?:[ .-]?\d){7,9}(?!\d)")


class InteractionAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.controls: list[tuple[set[str], set[str]]] = []
        self.quotes: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        classes = set(values.get("class", "").split())
        if "bqp-quote" in classes:
            self.quotes.append((values.get("data-pid", ""), values.get("data-qid", "")))
        if "data-b-pids" in values or "data-b-qids" in values:
            pids = {value for value in values.get("data-b-pids", "").split(",") if value}
            qids = {value for value in values.get("data-b-qids", "").split(",") if value}
            self.controls.append((pids, qids))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True,
        encoding="utf-8",
    )
    return [line for line in result.stdout.splitlines() if line]


def check_schema_and_ids(participants, quotes, records) -> None:
    require(list(participants.columns) == PARTICIPANT_COLUMNS, "participants schema mismatch")
    require(list(quotes.columns) == QUOTE_COLUMNS, "quotes schema mismatch")
    require(list(records.columns) == RECORD_COLUMNS, "records schema mismatch")
    require(list(participants.pid) == [f"P{i:02d}" for i in range(1, 16)], "PID sequence mismatch")
    require(list(quotes.quote_id) == [f"Q{i:03d}" for i in range(1, 91)], "quote_id sequence mismatch")
    require(list(records.record_id) == [f"R{i:03d}" for i in range(1, 144)], "record_id sequence mismatch")
    require(list(records.pdf_entry_id) == list(range(1, 144)), "pdf_entry_id sequence mismatch")
    require(not participants.duplicated().any(), "duplicate participant row")
    require(not quotes.duplicated().any(), "duplicate quote row")
    require(not records.duplicated().any(), "duplicate record row")
    valid_pids = set(participants.pid)
    require(set(quotes.pid) <= valid_pids, "quote PID foreign-key mismatch")
    require(set(records.pid) <= valid_pids, "record PID foreign-key mismatch")
    require(set(quotes.pattern_id.dropna()) <= set(viz.PATTERN_META), "unknown pattern_id")
    require(quotes.ref_id.map(lambda value: bool(REF_RE.fullmatch(str(value)))).all(), "invalid quote ref_id")
    require(records.ref_id.map(lambda value: bool(REF_RE.fullmatch(str(value)))).all(), "invalid record ref_id")


def check_participant_privacy(participants) -> None:
    require(set(participants.age_group) <= {"18_29", "30_44", "45_plus", "unknown"}, "invalid age_group")
    require(set(participants.occupation) == ALLOWED_OCCUPATIONS, "occupation is not generalized")
    require(
        participants.note.fillna("").map(
            lambda value: value.startswith("Residence source:")
            or value == "Residence not coded: outside Vietnam region taxonomy."
        ).all(),
        "participant note contains non-provenance detail",
    )
    text = "\n".join(participants.astype(str).to_numpy().ravel())
    require(not EMAIL_RE.search(text), "email-like value found in participants")
    require(not PHONE_RE.search(text), "phone-like value found in participants")


def check_wtp(participants) -> None:
    mins = pd.to_numeric(participants.wtp_min, errors="coerce")
    maxs = pd.to_numeric(participants.wtp_max, errors="coerce")
    require(not (mins.dropna() < 0).any(), "negative wtp_min")
    require(not (maxs.dropna() < 0).any(), "negative wtp_max")
    require(not ((mins > maxs) & mins.notna() & maxs.notna()).any(), "wtp_min exceeds wtp_max")


def check_tracker(quotes, tracker) -> None:
    require(list(tracker.columns) == TRACKER_COLUMNS, "hypothesis tracker schema mismatch")
    require(len(tracker) == len(viz.PATTERN_META) == 9, "hypothesis tracker row count mismatch")
    require(set(tracker.finding_id) == set(viz.PATTERN_META), "tracker finding IDs mismatch")
    require(set(tracker.cohort) == {"cohort_1"}, "unexpected tracker cohort")
    require(set(tracker.status) == {"new"}, "cohort_1 tracker status must be new")
    for row in tracker.itertuples(index=False):
        distinct_pids = int(quotes.loc[quotes.pattern_id == row.finding_id, "pid"].nunique())
        quote_rows = int((quotes.pattern_id == row.finding_id).sum())
        expected_delta = f"{distinct_pids} participants / {quote_rows} curated rows"
        require(row.evidence_delta == expected_delta, f"tracker evidence mismatch for {row.finding_id}")
        expected_confidence = CONFIDENCE_TO_CSV[viz.PATTERN_META[row.finding_id]["confidence"]]
        require(row.confidence_after == expected_confidence, f"tracker confidence mismatch for {row.finding_id}")
    require("Hai nguồn" in viz.PATTERN_META["P6"]["note"], "P6 caveat is stale")
    require(viz.PATTERN_META["S1"]["industry_leaning"], "S1 industry caveat missing")
    require(viz.PATTERN_META["S2"]["industry_leaning"], "S2 industry caveat missing")


def check_boolean_rendering(participants) -> None:
    for column in (
        "prefers_selftour", "companion_dependent", "price_sensitive",
        "experience_over_resort", "cares_about_authenticity",
    ):
        stats = viz._deck_bool_stats(participants, column)
        require(stats["true"] + stats["false"] + stats["unknown"] == len(participants), f"boolean totals mismatch for {column}")
        require("chưa mã hoá" in viz._deck_bool_label(stats), f"unknown label missing for {column}")
    decision_html = viz.render_decision_deck_visual(participants)
    archetype_html = viz.render_archetype_deck_visual(participants)
    require("chưa mã hoá" in decision_html, "decision visual hides unknown boolean values")
    require("chưa mã hoá" in archetype_html, "archetype visual hides unknown values")


def check_interactions(participants, quotes) -> None:
    for index in range(1, 10):
        html = getattr(viz, f"render_b{index}_visual")(quotes, participants)
        audit = InteractionAudit()
        audit.feed(html)
        require(audit.quotes, f"B{index} has no evidence quotes")
        for pids, qids in audit.controls:
            matches = [
                (pid, qid) for pid, qid in audit.quotes
                if pid in pids or qid in qids
            ]
            require(matches, f"B{index} interactive control resolves to no evidence")


def check_tracked_artifacts() -> None:
    tracked = git_lines("ls-files")
    require(
        not any(".quarto_ipynb_" in path or path.endswith(".quarto_ipynb") for path in tracked),
        "Quarto execution artifact is still tracked",
    )
    raw_files = [path for path in tracked if "/data/raw/" in path]
    require(raw_files == ["studies/pretour-research-2026/data/raw/.gitkeep"], "private raw file is tracked")


def main() -> int:
    participants = pd.read_csv(DATA / "participants.csv", keep_default_na=False)
    quotes = pd.read_csv(DATA / "quotes.csv")
    records = pd.read_csv(DATA / "records.csv")
    tracker = pd.read_csv(DATA / "hypothesis_tracker.csv", keep_default_na=False)
    require(len(participants) == 15, "participant count must be 15")
    require(len(records) == 143, "record count must be 143")
    require(len(quotes) == 90, "quote count must be 90")
    check_schema_and_ids(participants, quotes, records)
    check_participant_privacy(participants)
    check_wtp(participants)
    check_tracker(quotes, tracker)
    check_boolean_rendering(participants)
    check_interactions(participants, quotes)
    check_tracked_artifacts()
    print("OK: repository data, privacy, metadata, and interactions validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
