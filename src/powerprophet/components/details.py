import dash_bootstrap_components as dbc
from dash import dcc, html

details = dbc.Card(
    [
        dbc.CardHeader(
            html.Span(
                [html.I(className="fa fa-chart-line me-2"), "Forecast detail"]
            ),
            className="fw-semibold border-0 bg-transparent pt-3 pb-0",
        ),
        dbc.CardBody(
            dbc.Tabs(
                [
                    dbc.Tab(
                        label="Combined",
                        tab_id="tab-combined-uncertainty",
                        children=[
                            dcc.Graph(
                                id="combined-uncertainty-chart",
                                config={"displayModeBar": False},
                                style={"height": "450px"},
                                className="mt-3",
                            )
                        ],
                    ),
                    dbc.Tab(
                        label="Single q0.5",
                        tab_id="tab-future",
                        children=[
                            dcc.Graph(
                                id="future-forecast-chart",
                                config={"displayModeBar": False},
                                style={"height": "450px"},
                                className="mt-3",
                            )
                        ],
                    ),
                    dbc.Tab(
                        label="Ensemble medians",
                        tab_id="tab-ensemble-medians",
                        children=[
                            dcc.Graph(
                                id="ensemble-medians-chart",
                                config={"displayModeBar": False},
                                style={"height": "450px"},
                                className="mt-3",
                            )
                        ],
                    ),
                    dbc.Tab(
                        label="Quantiles by Ensemble",
                        tab_id="tab-member-quantiles",
                        children=[
                            html.Div(
                                [
                                    html.Label(
                                        "Weather ensemble member",
                                        className="small mb-1",
                                    ),
                                    dcc.Slider(
                                        id="ensemble-member-select",
                                        min=0,
                                        max=49,
                                        step=1,
                                        value=0,
                                        marks={0: "0", 24: "24", 49: "49"},
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": False,
                                        },
                                    ),
                                ],
                                className="mt-3",
                            ),
                            dcc.Graph(
                                id="member-quantiles-chart",
                                config={"displayModeBar": False},
                                style={"height": "450px"},
                            ),
                        ],
                    ),
                    dbc.Tab(
                        label="All",
                        tab_id="tab-all-quantiles",
                        children=[
                            dcc.Graph(
                                id="all-ensemble-quantiles-chart",
                                config={"displayModeBar": False},
                                style={"height": "450px"},
                                className="mt-3",
                            )
                        ],
                    ),
                ],
                id="detail-tabs",
                active_tab="tab-combined-uncertainty",
            )
        ),
    ]
)
