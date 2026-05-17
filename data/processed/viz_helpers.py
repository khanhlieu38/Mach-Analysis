"""Reusable plotly + HTML helpers for the MẠCH non-participant report."""

from collections import Counter
import plotly.graph_objects as go

PALETTE = {
    "neg": "#C0392B",
    "pos": "#27AE60",
    "accent": "#D4A574",
    "dim": "#BDC3C7",
    "ink": "#2C3E50",
    "warm_scale": ["#FFF5E6", "#FFD9A8", "#F4A261", "#E76F51", "#C0392B"],
}

CONFIDENCE_COLORS = {
    "Cao": "#27AE60",
    "Trung bình": "#F39C12",
    "Tín hiệu sớm": "#95A5A6",
}


def diverging_bar(interviews, neg_keywords, pos_keywords):
    """Diverging horizontal bar: negative signals (left) vs positive (right) per person."""
    rows = []
    for pid, data in interviews.items():
        text = " ".join([
            data["concept_reaction"]["first_impression"],
            data["concept_reaction"].get("would_join", ""),
        ]).lower()
        neg_hits = [kw for kw in neg_keywords if kw in text]
        pos_hits = [kw for kw in pos_keywords if kw in text]
        rows.append({
            "pid": pid,
            "neg_n": len(neg_hits),
            "pos_n": len(pos_hits),
            "neg_kw": ", ".join(neg_hits) or "—",
            "pos_kw": ", ".join(pos_hits) or "—",
        })

    pids = [r["pid"] for r in rows]
    fig = go.Figure()
    fig.add_bar(
        y=pids,
        x=[-r["neg_n"] for r in rows],
        orientation="h",
        name="Tín hiệu tiêu cực",
        marker_color=PALETTE["neg"],
        customdata=[r["neg_kw"] for r in rows],
        hovertemplate="<b>%{y}</b><br>%{customdata}<extra></extra>",
    )
    fig.add_bar(
        y=pids,
        x=[r["pos_n"] for r in rows],
        orientation="h",
        name="Tín hiệu tích cực",
        marker_color=PALETTE["pos"],
        customdata=[r["pos_kw"] for r in rows],
        hovertemplate="<b>%{y}</b><br>%{customdata}<extra></extra>",
    )
    fig.update_layout(
        barmode="relative",
        title="Phản ứng với concept card — phân hóa: 2/4 tiêu cực áp đảo, 2/4 tích cực kèm qualifier",
        xaxis_title="Số tín hiệu trong phản ứng đầu tiên",
        yaxis_title="",
        height=360,
        margin=dict(l=60, r=20, t=60, b=40),
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="white",
    )
    fig.update_xaxes(zeroline=True, zerolinecolor=PALETTE["ink"], zerolinewidth=1)
    return fig


def keyword_bar(interviews):
    """Horizontal bar of ideal-experience keyword frequency."""
    all_kws = []
    who_said = {}
    for pid, data in interviews.items():
        for kw in data["ideal_experience"]["keywords"]:
            all_kws.append(kw)
            who_said.setdefault(kw, []).append(pid)

    counts = Counter(all_kws)
    items = counts.most_common()
    kws = [k for k, _ in items][::-1]
    vals = [v for _, v in items][::-1]
    who = ["<br>".join(who_said[k]) for k in kws]

    fig = go.Figure(go.Bar(
        x=vals,
        y=kws,
        orientation="h",
        marker=dict(
            color=vals,
            colorscale=PALETTE["warm_scale"],
            showscale=False,
        ),
        customdata=who,
        hovertemplate="<b>%{y}</b><br>Tần suất: %{x}/4<br>Người nhắc:<br>%{customdata}<extra></extra>",
    ))
    fig.update_layout(
        title="Từ khóa trải nghiệm lý tưởng — không ai nhắc 'kiến thức'",
        xaxis_title="Số người nhắc (n=4)",
        yaxis_title="",
        height=max(380, 26 * len(kws)),
        margin=dict(l=140, r=20, t=60, b=40),
        plot_bgcolor="white",
    )
    return fig


def barrier_heatmap(interviews, barrier_categories):
    """Heatmap: rows = barrier categories, cols = people. Binary fill + raw text hover."""
    pids = list(interviews.keys())
    cats = list(barrier_categories.keys())
    z, text_matrix = [], []

    for cat, keywords in barrier_categories.items():
        row, text_row = [], []
        for pid in pids:
            barriers = interviews[pid]["barriers"]
            matched = [b for b in barriers if any(kw in b.lower() for kw in keywords)]
            row.append(1 if matched else 0)
            text_row.append("<br>".join(f"• {b}" for b in matched) if matched else "—")
        z.append(row)
        text_matrix.append(text_row)

    fig = go.Figure(go.Heatmap(
        z=z,
        x=pids,
        y=cats,
        text=text_matrix,
        hovertemplate="<b>%{y}</b> — %{x}<br>%{text}<extra></extra>",
        colorscale=[[0, "#F8F9FA"], [1, PALETTE["accent"]]],
        showscale=False,
        xgap=4, ygap=4,
    ))
    fig.update_layout(
        title="Ma trận barriers × người — 'Kiến thức quá nặng' xuất hiện ở 4/4",
        height=380,
        margin=dict(l=220, r=20, t=60, b=40),
        plot_bgcolor="white",
    )
    fig.update_yaxes(autorange="reversed")
    return fig


# ───────── HTML helpers ─────────

def kpi_tiles(items):
    """4 KPI tiles in a row. items = [{label, value, sub}]."""
    cards = "".join(
        f'<div class="kpi"><div class="kpi-value">{i["value"]}</div>'
        f'<div class="kpi-label">{i["label"]}</div>'
        f'<div class="kpi-sub">{i["sub"]}</div></div>'
        for i in items
    )
    return f'<div class="kpi-row">{cards}</div>'


def finding_badges(findings):
    """Finding pills with confidence badge."""
    rows = ""
    for f in findings:
        color = CONFIDENCE_COLORS[f["tier"]]
        rows += (
            f'<div class="finding">'
            f'<span class="badge" style="background:{color}">{f["tier"]}</span>'
            f'<span class="finding-text">{f["label"]}</span>'
            f'</div>'
        )
    return f'<div class="findings-list">{rows}</div>'


def profile_cards(interviews):
    """2x2 grid of profile cards."""
    cards = ""
    for pid, data in interviews.items():
        p = data["profile"]
        cards += (
            f'<div class="profile">'
            f'<div class="profile-id">{pid}</div>'
            f'<div class="profile-row"><span>Tuổi</span><b>{p["age_group"]}</b></div>'
            f'<div class="profile-row"><span>Nghề</span><b>{p["occupation_category"]}</b></div>'
            f'<div class="profile-row"><span>Budget</span><b>{p["travel_budget_range"]}</b></div>'
            f'<div class="profile-row"><span>Style</span><b>{p["travel_style"]}</b></div>'
            f'<div class="profile-row"><span>Decision</span><b>{p["decision_style"]}</b></div>'
            f'</div>'
        )
    return f'<div class="profile-grid">{cards}</div>'


def quote_cards(interviews, field_path, title_field=None):
    """Quote cards. field_path = ('concept_reaction', 'first_impression')."""
    cards = ""
    for pid, data in interviews.items():
        node = data
        for k in field_path:
            node = node[k]
        title = ""
        if title_field:
            tnode = data
            for k in title_field:
                tnode = tnode[k]
            title = f'<div class="quote-title">{tnode}</div>'
        cards += (
            f'<div class="quote-card">'
            f'<div class="quote-attr">{pid}</div>'
            f'{title}'
            f'<div class="quote-text">"{node}"</div>'
            f'</div>'
        )
    return f'<div class="quote-grid">{cards}</div>'


def recommendations_table(recs):
    """Recommendation rows with badge + owner pill."""
    rows = ""
    for i, r in enumerate(recs, 1):
        color = CONFIDENCE_COLORS[r["confidence"]]
        rows += (
            f'<div class="rec-row">'
            f'<div class="rec-num">{i}</div>'
            f'<div class="rec-body">'
            f'<div class="rec-change">{r["change"]}</div>'
            f'<div class="rec-evidence">Evidence: {r["evidence"]}</div>'
            f'</div>'
            f'<div class="rec-side">'
            f'<span class="badge" style="background:{color}">{r["confidence"]}</span>'
            f'<span class="owner">{r["owner"]}</span>'
            f'</div>'
            f'</div>'
        )
    return f'<div class="rec-list">{rows}</div>'
