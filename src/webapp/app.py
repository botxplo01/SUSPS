from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


def create_dash_app(requests_pathname_prefix: str = "/") -> Dash:
    # External stylesheets
    external_stylesheets = [dbc.themes.BOOTSTRAP]

    app = Dash(
        __name__,
        requests_pathname_prefix=requests_pathname_prefix,
        external_stylesheets=external_stylesheets,
        suppress_callback_exceptions=True,
        title="SUSPS Dashboard",
    )

    # Simple sample chart without pandas
    modules = ["Growth", "Energy", "Traffic"]
    readiness = [10, 5, 2]
    fig = go.Figure(
        data=[go.Bar(x=modules, y=readiness, marker_color="#1f77b4")],
        layout=go.Layout(title_text="Initial Module Readiness (placeholder)")
    )

    navbar = dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("SUSPS", href="#"),
            dbc.Nav(
                [
                    dbc.NavItem(dbc.NavLink("Dashboard", href=requests_pathname_prefix)),
                ],
                className="ms-auto",
                navbar=True,
            ),
        ]),
        color="dark",
        dark=True,
        className="mb-4",
    )

    app.layout = dbc.Container([
        navbar,
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Welcome"),
                    dbc.CardBody([
                        html.P("Smart Urban Simulation and Prediction System"),
                        html.Ul([
                            html.Li("Urban Growth (coming soon)"),
                            html.Li("Energy Forecasting (coming soon)"),
                            html.Li("Traffic Simulation (coming soon)"),
                        ])
                    ])
                ])
            ], width=4),
            dbc.Col([
                dcc.Graph(figure=fig)
            ], width=8)
        ])
    ], fluid=True)

    return app
