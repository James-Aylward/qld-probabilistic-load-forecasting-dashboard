"""Plotly versions of the exploratory matplotlib plots.

Each function takes the full predictions dataframe plus a substation
name (and, for `member_quantiles_figure`, an ensemble member index) and
returns a `plotly.graph_objects.Figure` ready to hand to a `dcc.Graph`.
"""

import re

import numpy as np
import plotly.graph_objects as go
import polars as pl
from plotly.colors import sample_colorscale

ENS_QUANTILE_RE = re.compile(r"ens(\d+)_q([\d.]+)")

QUANTILE_ALPHA = {
    0.02: 0.10,
    0.10: 0.14,
    0.25: 0.20,
    0.50: 0.75,
    0.75: 0.20,
    0.90: 0.14,
    0.98: 0.10,
}

QUANTILE_WIDTH = {
    0.02: 0.5,
    0.10: 0.6,
    0.25: 0.8,
    0.50: 1.4,
    0.75: 0.8,
    0.90: 0.6,
    0.98: 0.5,
}

BAND_PAIRS = [
    (0.02, 0.98, 0.12, "2nd\u201398th percentile"),
    (0.10, 0.90, 0.20, "10th\u201390th percentile"),
    (0.25, 0.75, 0.32, "25th\u201375th percentile"),
]


def _empty_figure(message: str = "Select a substation") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16},
            }
        ],
    )
    return fig


def _columns_by_quantile(columns: list[str]) -> dict[float, list[str]]:
    """Group ensemble prediction columns by quantile level."""
    groups: dict[float, list[str]] = {}
    for c in columns:
        m = ENS_QUANTILE_RE.fullmatch(c)
        if m:
            groups.setdefault(float(m.group(2)), []).append(c)
    return dict(sorted(groups.items()))


def _substation_frame(df: pl.DataFrame, substation: str) -> pl.DataFrame:
    return df.filter(pl.col("Name") == substation).sort("datetime")


def _prediction_columns(columns: list[str]) -> list[str]:
    return [c for c in columns if ENS_QUANTILE_RE.fullmatch(c)]


def _rgba(rgb: str, alpha: float) -> str:
    """Convert a plotly 'rgb(r, g, b)' string into 'rgba(r, g, b, alpha)'."""
    r, g, b = rgb[4:-1].split(",")
    return f"rgba({r.strip()},{g.strip()},{b.strip()},{alpha})"


def _add_band(
    fig: go.Figure,
    x,
    low,
    high,
    color: str,
    alpha: float,
    label: str,
) -> None:
    fig.add_scatter(
        x=x,
        y=high,
        mode="lines",
        line={"width": 0},
        showlegend=False,
        hoverinfo="skip",
    )
    fig.add_scatter(
        x=x,
        y=low,
        mode="lines",
        line={"width": 0},
        fill="tonexty",
        fillcolor=_rgba(color, alpha),
        name=label,
    )


def future_forecast_figure(df: pl.DataFrame, substation: str) -> go.Figure:
    frame = _substation_frame(df, substation)
    if frame.is_empty():
        return _empty_figure()

    fig = go.Figure()

    past_frame = frame.filter(~pl.col("is_future"))

    fig.add_scatter(
        x=past_frame["datetime"],
        y=past_frame["MW"],
        mode="lines",
        name="Actual",
    )
    fig.add_scatter(
        x=frame["datetime"],
        y=frame["forecast_median"],
        mode="lines",
        name="Forecast",
    )

    fig.update_layout(
        title=substation,
        xaxis_title="Time",
        yaxis_title="MW",
        hovermode="x unified",
    )
    return fig


def all_ensemble_quantiles_figure(
    df: pl.DataFrame, substation: str
) -> go.Figure:
    frame = _substation_frame(df, substation)
    if frame.is_empty():
        return _empty_figure()

    prediction_cols = _prediction_columns(frame.columns)
    if not prediction_cols:
        return _empty_figure("No ensemble predictions available")

    members = sorted(
        {int(ENS_QUANTILE_RE.fullmatch(c).group(1)) for c in prediction_cols}
    )
    quantiles = sorted(
        {float(ENS_QUANTILE_RE.fullmatch(c).group(2)) for c in prediction_cols}
    )

    colors = sample_colorscale("Turbo", np.linspace(0, 1, len(members)))
    member_colors = dict(zip(members, colors))

    fig = go.Figure()

    actual = frame.filter(~pl.col("is_future"))
    fig.add_scatter(
        x=actual["datetime"],
        y=actual["MW"],
        mode="lines",
        name="Actual MW",
        line={"color": "black", "width": 3},
    )

    for member in members:
        color = member_colors[member]
        for quantile in quantiles:
            col = f"ens{member}_q{quantile:g}"
            if col not in frame.columns:
                continue
            series = frame.select("datetime", col).drop_nulls(col)
            if series.is_empty():
                continue
            fig.add_scatter(
                x=series["datetime"],
                y=series[col],
                mode="lines",
                line={
                    "color": _rgba(color, QUANTILE_ALPHA.get(quantile, 0.15)),
                    "width": QUANTILE_WIDTH.get(quantile, 0.7),
                },
                showlegend=False,
                hoverinfo="skip",
            )

    forecast_start = frame.filter(
        pl.any_horizontal(pl.col(prediction_cols).is_not_null())
    )["datetime"].min()
    if forecast_start is not None:
        fig.add_vline(x=forecast_start, line_dash="dot", line_color="black")

    fig.update_layout(
        title=substation,
        xaxis_title="Datetime",
        yaxis_title="MW",
        hovermode="x unified",
        showlegend=True,
    )
    return fig


def combined_uncertainty_figure(df: pl.DataFrame, substation: str) -> go.Figure:
    frame = _substation_frame(df, substation)
    if frame.is_empty():
        return _empty_figure()

    prediction_cols = _prediction_columns(frame.columns)
    if not prediction_cols:
        return _empty_figure("No ensemble predictions available")

    # Mean across ensemble members at each quantile level (nulls ignored)
    frame = frame.with_columns(
        pl.mean_horizontal(cols).alias(f"combined_q{q:g}")
        for q, cols in _columns_by_quantile(prediction_cols).items()
    )

    actual = frame.filter(~pl.col("is_future"))
    forecast = frame.drop_nulls("combined_q0.5")

    fig = go.Figure()
    fig.add_scatter(
        x=actual["datetime"],
        y=actual["MW"],
        mode="lines",
        name="Actual MW",
        line={"color": "black", "width": 2.5},
    )

    purple = "rgb(148,103,189)"
    for low, high, alpha, label in BAND_PAIRS:
        _add_band(
            fig,
            forecast["datetime"],
            forecast[f"combined_q{low:g}"],
            forecast[f"combined_q{high:g}"],
            purple,
            alpha,
            label,
        )

    fig.add_scatter(
        x=forecast["datetime"],
        y=forecast["combined_q0.5"],
        mode="lines",
        name="Combined median",
        line={"color": purple, "width": 2.5},
    )

    if not forecast.is_empty():
        fig.add_vline(
            x=forecast["datetime"].min(), line_dash="dash", line_color="grey"
        )

    fig.update_layout(
        title=substation,
        xaxis_title="Datetime",
        yaxis_title="MW",
        hovermode="x unified",
    )
    return fig


def member_quantiles_figure(
    df: pl.DataFrame, substation: str, member: int
) -> go.Figure:
    frame = _substation_frame(df, substation)
    if frame.is_empty():
        return _empty_figure()

    prefix = f"ens{member}"
    required = [
        f"{prefix}_q{q:g}" for q in (0.02, 0.1, 0.25, 0.5, 0.75, 0.9, 0.98)
    ]
    missing = [c for c in required if c not in frame.columns]
    if missing:
        return _empty_figure(f"No predictions for ensemble member {member}")

    actual = frame.filter(~pl.col("is_future"))
    forecast = frame.drop_nulls(f"{prefix}_q0.5")

    fig = go.Figure()
    fig.add_scatter(
        x=actual["datetime"],
        y=actual["MW"],
        mode="lines",
        name="Actual MW",
        line={"color": "black", "width": 2.5},
    )

    blue = "rgb(31,119,180)"
    for low, high, alpha, label in BAND_PAIRS:
        _add_band(
            fig,
            forecast["datetime"],
            forecast[f"{prefix}_q{low:g}"],
            forecast[f"{prefix}_q{high:g}"],
            blue,
            alpha,
            label,
        )

    fig.add_scatter(
        x=forecast["datetime"],
        y=forecast[f"{prefix}_q0.5"],
        mode="lines",
        name="Median forecast",
        line={"color": blue, "width": 2.5},
    )

    if not forecast.is_empty():
        fig.add_vline(
            x=forecast["datetime"].min(), line_dash="dash", line_color="grey"
        )

    fig.update_layout(
        title=substation,
        xaxis_title="Datetime",
        yaxis_title="MW",
        hovermode="x unified",
    )
    return fig


def ensemble_medians_figure(df: pl.DataFrame, substation: str) -> go.Figure:
    frame = _substation_frame(df, substation)
    if frame.is_empty():
        return _empty_figure()

    median_cols = sorted(
        (c for c in frame.columns if re.fullmatch(r"ens\d+_q0\.5", c)),
        key=lambda c: int(re.search(r"ens(\d+)", c).group(1)),
    )
    if not median_cols:
        return _empty_figure("No ensemble predictions available")

    actual = frame.filter(~pl.col("is_future"))

    fig = go.Figure()
    fig.add_scatter(
        x=actual["datetime"],
        y=actual["MW"],
        mode="lines",
        name="Actual MW",
        line={"color": "black", "width": 2.5},
    )

    for i, col in enumerate(median_cols):
        series = frame.drop_nulls(col)
        fig.add_scatter(
            x=series["datetime"],
            y=series[col],
            mode="lines",
            line={"color": "rgba(31,119,180,0.16)", "width": 1},
            name="Ensemble-member medians",
            legendgroup="member-medians",
            showlegend=(i == 0),
            hoverinfo="skip",
        )

    # mean_horizontal is null only where every member is null, so these
    # rows are also where any member has a forecast
    ensemble_mean = frame.select(
        "datetime", pl.mean_horizontal(median_cols).alias("mean")
    ).drop_nulls("mean")
    fig.add_scatter(
        x=ensemble_mean["datetime"],
        y=ensemble_mean["mean"],
        mode="lines",
        name="Mean of member medians",
        line={"color": "rgb(31,119,180)", "width": 2.5},
    )

    if not ensemble_mean.is_empty():
        fig.add_vline(
            x=ensemble_mean["datetime"].min(),
            line_dash="dash",
            line_color="grey",
        )

    fig.update_layout(
        title=substation,
        xaxis_title="Datetime",
        yaxis_title="MW",
        hovermode="x unified",
    )
    return fig
