from datetime import datetime

import dash_leaflet as dl
import polars as pl
from dash import ALL, Input, Output, callback, ctx, no_update

from powerprophet.components import plots
from powerprophet.components.sidebar import get_names

MIN_RADIUS = 3
MAX_RADIUS = 20


def _get_radius(value, rmin, rmax, tmin=MIN_RADIUS, tmax=MAX_RADIUS) -> float:
    if rmax == rmin:
        return (tmin + tmax) / 2
    return (value - rmin) / (rmax - rmin) * (tmax - tmin) + tmin


def register_callbacks(df: pl.DataFrame, prediction_time: datetime):

    @callback(
        Output("selected-substation", "data"),
        Input({"type": "map-marker", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def select_substation(clicks):

        if not ctx.triggered:
            return no_update

        if all(c is None for c in clicks):
            return no_update

        return ctx.triggered_id["index"]

    @callback(
        Output("future-forecast-chart", "figure"),
        Input("selected-substation", "data"),
    )
    def update_future_forecast(selected_sub: str | None):
        if not selected_sub:
            return plots._empty_figure()
        return plots.future_forecast_figure(df, selected_sub)

    @callback(
        Output("ensemble-medians-chart", "figure"),
        Input("selected-substation", "data"),
        Input("detail-tabs", "active_tab"),
    )
    def update_ensemble_medians(selected_sub: str | None, active_tab: str):
        if active_tab != "tab-ensemble-medians":
            return no_update
        if not selected_sub:
            return plots._empty_figure()
        return plots.ensemble_medians_figure(df, selected_sub)

    @callback(
        Output("combined-uncertainty-chart", "figure"),
        Input("selected-substation", "data"),
        Input("detail-tabs", "active_tab"),
    )
    def update_combined_uncertainty(selected_sub: str | None, active_tab: str):
        if active_tab != "tab-combined-uncertainty":
            return no_update
        if not selected_sub:
            return plots._empty_figure()
        return plots.combined_uncertainty_figure(df, selected_sub)

    @callback(
        Output("member-quantiles-chart", "figure"),
        Input("selected-substation", "data"),
        Input("detail-tabs", "active_tab"),
        Input("ensemble-member-select", "value"),
    )
    def update_member_quantiles(
        selected_sub: str | None, active_tab: str, member: int
    ):
        if active_tab != "tab-member-quantiles":
            return no_update
        if not selected_sub:
            return plots._empty_figure()
        return plots.member_quantiles_figure(df, selected_sub, member)

    @callback(
        Output("all-ensemble-quantiles-chart", "figure"),
        Input("selected-substation", "data"),
        Input("detail-tabs", "active_tab"),
    )
    def update_all_ensemble_quantiles(
        selected_sub: str | None, active_tab: str
    ):
        if active_tab != "tab-all-quantiles":
            return no_update
        if not selected_sub:
            return plots._empty_figure()
        return plots.all_ensemble_quantiles_figure(df, selected_sub)

    @callback(
        Output("hierarchy-value", "options"),
        Output("hierarchy-value", "value"),
        Input("hierarchy-level", "value"),
    )
    def update_filter_options(level: str):
        # Reset the filter to "All" whenever the level changes
        return get_names(df, level), None

    @callback(
        Output("substation-markers", "children"),
        Input("time-cursor", "value"),
        Input("remove-direct-connections-checkbox", "value"),
        Input("hierarchy-level", "value"),
        Input("hierarchy-value", "value"),
    )
    def update_markers(
        hours_offset: int,
        remove_dc: bool,
        level: str,
        name_filter: str | None,
    ):

        markers = []

        # Only show series at the selected hierarchy level
        frame = df.filter(pl.col("Hierarchy") == level)

        if remove_dc:
            frame = frame.filter(
                ~pl.col("Name").str.contains("Direct Connections")
            )

        if frame.is_empty():
            return markers

        # Radii scale should be constant for this particular prediction set.
        # It is computed per level, since a State total dwarfs a substation.
        rmin = abs(frame["MW"]).min()
        rmax = abs(frame["MW"]).max()

        # Filter to a single Name only after the radius scale is fixed, so
        # the marker size stays comparable with the unfiltered view.
        if name_filter:
            frame = frame.filter(pl.col("Name") == name_filter)

        zero_time_idx = df.filter(pl.col("datetime") == prediction_time).row(
            0, named=True
        )["time_idx"]

        frame = frame.with_columns(pl.col("time_idx") - zero_time_idx)
        frame = frame.filter(pl.col("time_idx") == hours_offset)

        for row in frame.iter_rows(named=True):
            if row["is_future"]:
                mw = row["forecast_median"]
                label = "Forecast"
            else:
                mw = row["MW"]
                label = "Actual"

            radius = _get_radius(mw, rmin, rmax)

            markers.append(
                dl.CircleMarker(
                    center=[
                        row["lat"],
                        row["long"],
                    ],
                    id={"type": "map-marker", "index": row["Name"]},
                    radius=radius,
                    fillOpacity=0.75,
                    children=[
                        dl.Tooltip(f"{row['Name']}\n{label}: {mw:.1f} MW\n")
                    ],
                )
            )

        return markers
