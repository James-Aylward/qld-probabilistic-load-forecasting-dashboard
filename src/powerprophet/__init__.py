import os
from datetime import datetime
from pathlib import Path

import dash_bootstrap_components as dbc
import polars as pl
from dash import Dash, dcc, html

from powerprophet.components.callbacks import register_callbacks
from powerprophet.components.details import details
from powerprophet.components.map import build_map
from powerprophet.components.navbar import build_navbar
from powerprophet.components.sidebar import build_sidebar

try:
    PREDICTIONS_DIR = Path(os.environ["POWERPROPHET_PREDICTIONS_DIR"])
except KeyError:
    raise SystemExit(
        "POWERPROPHET_PREDICTIONS_DIR is not set. Point it at the directory "
        "containing the prediction parquet files (see .env.example)."
    ) from None
PREDICTION_FILE = max(PREDICTIONS_DIR.glob("*.parquet"), key=lambda p: p.name)
QLD_CENTER = (-22.55, 144.02)

FILE_TIME_FMT = "%Y-%m-%d_%H-%M"

PREDICTION_TIME = datetime.strptime(PREDICTION_FILE.stem, FILE_TIME_FMT)
df = pl.read_parquet(PREDICTION_FILE)

print(f"Loading predictions from {PREDICTION_TIME}")

median_cols = [col for col in df.columns if col.endswith("_q0.5")]

df = df.with_columns(
    pl.concat_list(median_cols).list.median().alias("forecast_median")
)


def build_layout(app: Dash):
    return html.Div(
        [
            dcc.Store(id="selected-substation", data=None),
            build_navbar(),
            dbc.Container(
                dbc.Row(
                    [
                        dbc.Col(
                            build_sidebar(df),
                            width=12,
                            lg=3,
                            className="mb-4 mb-lg-0",
                        ),
                        dbc.Col(
                            [
                                build_map(QLD_CENTER),
                                html.Div(className="mb-4"),
                                details,
                            ],
                            width=12,
                            lg=9,
                        ),
                    ]
                ),
                fluid="lg",
                className="pb-5",
            ),
        ],
    )


def main() -> None:
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
        title="PowerProphet",
    )
    app.layout = build_layout(app)
    register_callbacks(df, PREDICTION_TIME)
    app.run(debug=True)
