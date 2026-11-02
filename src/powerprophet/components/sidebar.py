import dash_bootstrap_components as dbc
import polars as pl
from dash import dcc, html

# Display order for the hierarchy levels, lowest level first. Any level found
# in the data that isn't listed here is appended at the end.
HIERARCHY_ORDER = ["Substation", "Zone", "QLD Split", "State"]


def get_hierarchy_levels(df: pl.DataFrame) -> list[str]:
    """Distinct values of the "Hierarchy" column, in display order."""
    present = set(df["Hierarchy"].unique().to_list())
    ordered = [lvl for lvl in HIERARCHY_ORDER if lvl in present]
    extras = sorted(present - set(ordered))
    return ordered + extras


def get_names(df: pl.DataFrame, level: str) -> list[str]:
    """Sorted distinct series Names at a given hierarchy level."""
    return sorted(
        df.filter(pl.col("Hierarchy") == level)["Name"].unique().to_list()
    )


def build_sidebar(df: pl.DataFrame) -> dbc.Card:
    levels = get_hierarchy_levels(df)

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div("Filters", className="pp-label"),
                dbc.Checkbox(
                    id="remove-direct-connections-checkbox",
                    label="Remove direct connections",
                    value=False,
                ),
                html.Label("Hierarchy level", className="small mb-1"),
                dbc.Select(
                    id="hierarchy-level",
                    options=[{"label": lvl, "value": lvl} for lvl in levels],
                    value=levels[0],
                    className="mb-3",
                ),
                html.Label("Filter value", className="small mb-1"),
                dcc.Dropdown(
                    id="hierarchy-value",
                    options=get_names(df, levels[0]),
                    value=None,
                    placeholder="All (type to search)",
                    searchable=True,
                    clearable=True,
                    className="mb-4",
                ),
                html.Hr(className="my-3"),
                html.Div("Selected substation", className="pp-label"),
                html.Div(id="selected-substation-summary"),
            ]
        ),
        className="h-100",
    )
