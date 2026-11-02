import dash_bootstrap_components as dbc
from dash import Input, Output, clientside_callback, html

_theme_switcher = html.Span(
    [
        html.I(className="fa fa-moon me-2"),
        dbc.Switch(
            id="theme-switch",
            value=True,
            className="d-inline-block",
            persistence=True,
        ),
        html.I(className="fa fa-sun ms-2"),
    ],
    className="d-flex align-items-center",
)

clientside_callback(
    """
    (switchOn) => {
       document.documentElement.setAttribute("data-bs-theme", switchOn ? "light" : "dark");
       return window.dash_clientside.no_update
    }
    """,
    Output("theme-switch", "id"),
    Input("theme-switch", "value"),
)


def build_navbar() -> dbc.NavbarSimple:
    return dbc.NavbarSimple(
        children=[
            _theme_switcher,
        ],
        brand="PowerProphet",
        color="primary",
        dark=True,
        fluid=True,
        className="mb-4 px-3",
    )
