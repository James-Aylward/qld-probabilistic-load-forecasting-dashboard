import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import dcc, html


def build_map(map_center: tuple[float, float]):
    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span(
                    [
                        html.I(className="fa fa-map-location-dot me-2"),
                        "Network map",
                    ]
                ),
                className="fw-semibold border-0 bg-transparent pt-3 pb-0",
            ),
            dbc.CardBody(
                [
                    dl.Map(
                        id="substation-map",
                        center=map_center,
                        attributionControl=False,
                        zoom=6,
                        style={
                            "width": "100%",
                            "height": "600px",
                            "position": "relative",
                        },
                        children=[
                            dl.TileLayer(),
                            dl.LayerGroup(id="substation-markers"),
                        ],
                    ),
                    html.Div(
                        [
                            html.I(
                                className="fa fa-clock-rotate-left me-2 text-muted"
                            ),
                            dcc.Slider(
                                id="time-cursor",
                                min=-23,
                                max=24,
                                step=1,
                                value=0,
                                marks={
                                    -23: "Encoder Start",
                                    0: "t=0",
                                    24: "+24h",
                                },
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": False,
                                },
                                className="flex-grow-1",
                            ),
                        ],
                        className="d-flex align-items-center mt-4",
                    ),
                ]
            ),
        ]
    )
