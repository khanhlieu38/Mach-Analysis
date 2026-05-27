import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from collections import Counter

PALETTE = {
    "neg": "#C0392B",
    "pos": "#27AE60",
    "accent": "#D4A574",
    "dim": "#BDC3C7",
    "ink": "#2C3E50",
    "warm_scale": ["#FFF3E0", "#FFCC80", "#FFA726", "#EF6C00", "#BF360C"],
}

CONFIDENCE_COLORS = {
    "high": "#27AE60",
    "medium": "#F39C12",
    "early_signal": "#95A5A6",
}


def load_study_data(study_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load participants.csv + quotes.csv cho một study."""
    participants = pd.read_csv(study_dir / "data" / "participants.csv")
    quotes = pd.read_csv(study_dir / "data" / "quotes.csv")
    return participants, quotes


def diverging_bar(quotes_df: pd.DataFrame, neg_keywords: list, pos_keywords: list) -> go.Figure:
    """Diverging bar: phản ứng concept card theo từng participant.

    Scans rows where theme == 'concept_reaction' for keyword matches.
    """
    pids = quotes_df["pid"].unique()

    neg_counts, pos_counts, neg_hits, pos_hits = [], [], [], []
    for pid in pids:
        text = " ".join(
            quotes_df[
                (quotes_df["pid"] == pid) & (quotes_df["theme"] == "concept_reaction")
            ]["quote_full"].fillna("")
        )
        neg = [k for k in neg_keywords if k in text]
        pos = [k for k in pos_keywords if k in text]
        neg_counts.append(-len(neg))
        pos_counts.append(len(pos))
        neg_hits.append(", ".join(neg) or "—")
        pos_hits.append(", ".join(pos) or "—")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=list(pids), x=neg_counts, orientation="h",
        name="Tín hiệu tiêu cực", marker_color=PALETTE["neg"],
        customdata=neg_hits,
        hovertemplate="<b>%{y}</b>: %{customdata}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=list(pids), x=pos_counts, orientation="h",
        name="Tín hiệu tích cực", marker_color=PALETTE["pos"],
        customdata=pos_hits,
        hovertemplate="<b>%{y}</b>: %{customdata}<extra></extra>",
    ))
    fig.update_layout(
        barmode="relative", plot_bgcolor="white",
        title="Phản ứng với concept card",
        xaxis_title="Số keyword", yaxis_title="",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=60, r=20, t=50, b=60),
    )
    fig.update_xaxes(zeroline=True, zerolinecolor=PALETTE["ink"], zerolinewidth=1)
    return fig


def keyword_bar(quotes_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: tần suất keyword trải nghiệm lý tưởng.

    Expects rows where subtheme == 'ideal_keyword', quote_short = keyword text.
    """
    kw_rows = quotes_df[quotes_df["subtheme"] == "ideal_keyword"]
    counter = Counter(kw_rows["quote_short"].dropna())
    keywords = [k for k, _ in counter.most_common()]
    counts = [counter[k] for k in keywords]
    who = {
        k: ", ".join(kw_rows[kw_rows["quote_short"] == k]["pid"].tolist())
        for k in keywords
    }

    fig = go.Figure(go.Bar(
        x=counts, y=keywords, orientation="h",
        marker=dict(color=counts, colorscale=PALETTE["warm_scale"], showscale=False),
        customdata=[who[k] for k in keywords],
        hovertemplate="<b>%{y}</b>: %{x} lần (%{customdata})<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="white",
        title="Từ khóa trải nghiệm lý tưởng",
        xaxis_title="Số người nhắc",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=140, r=20, t=50, b=40),
        height=max(300, len(keywords) * 28),
    )
    return fig


def barrier_heatmap(quotes_df: pd.DataFrame, barrier_categories: dict) -> go.Figure:
    """Heatmap: barrier categories × participants (binary).

    barrier_categories = {'Category Name': ['keyword1', 'keyword2'], ...}
    Matches keywords against rows where theme == 'barrier'.
    """
    pids = sorted(quotes_df["pid"].unique())
    barrier_rows = quotes_df[quotes_df["theme"] == "barrier"]
    categories = list(barrier_categories.keys())

    z, text_matrix = [], []
    for cat in categories:
        keywords = barrier_categories[cat]
        row_z, row_text = [], []
        for pid in pids:
            pid_text = " ".join(
                barrier_rows[barrier_rows["pid"] == pid]["quote_full"].fillna("")
            )
            matched = [kw for kw in keywords if kw in pid_text]
            row_z.append(1 if matched else 0)
            row_text.append(", ".join(matched) if matched else "—")
        z.append(row_z)
        text_matrix.append(row_text)

    fig = go.Figure(go.Heatmap(
        z=z, x=pids, y=categories,
        text=text_matrix,
        hovertemplate="<b>%{y}</b> — %{x}: %{text}<extra></extra>",
        colorscale=[[0, "#F8F9FA"], [1, PALETTE["accent"]]],
        showscale=False,
        xgap=4, ygap=4,
    ))
    fig.update_layout(
        plot_bgcolor="white",
        title="Ma trận barriers × người",
        margin=dict(l=200, r=20, t=50, b=40),
    )
    fig.update_yaxes(autorange="reversed")
    return fig
