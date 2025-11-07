from dash import Dash, html, dcc
import dash_bootstrap_components as dbc


def create_dash_app(requests_pathname_prefix: str = "/dash/") -> Dash:
    external_stylesheets = [dbc.themes.BOOTSTRAP]

    dash_app = Dash(
        __name__,
        requests_pathname_prefix=requests_pathname_prefix,
        external_stylesheets=external_stylesheets,
        suppress_callback_exceptions=True,
    )

    dash_app.layout = html.Div(
        [
            html.H2("SUSPS Dashboard"),
            html.Div(
                [
                    dcc.Link("Dashboard Home", href=requests_pathname_prefix),
                    html.Span(" | "),
                    dcc.Link("API Health", href="/health"),
                ]
            ),
            html.Hr(),
            html.P("Placeholder dashboard. Add maps/charts later."),
        ],
        style={"padding": "1rem"},
    )

    return dash_app
