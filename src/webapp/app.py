from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import os
import requests

from src.models.growth import predict_growth as _predict_growth
from src.models.energy import daily_profile as _energy_profile
from src.models.traffic import daily_profile as _traffic_profile


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

    # Readiness chart
    modules = ["Growth", "Energy", "Traffic"]
    readiness = [10, 5, 2]
    fig_readiness = go.Figure(
        data=[go.Bar(x=modules, y=readiness, marker_color="#1f77b4")],
        layout=go.Layout(title_text="Initial Module Readiness (placeholder)"),
    )

    # Synthetic charts (no-DB) — keep data inline to avoid HTTP coupling at app-creation time
    growth_years = list(range(2025, 2031))
    growth_values = [int(800_000 * (1.03 ** (i))) for i in range(len(growth_years))]
    fig_growth = go.Figure(
        data=[
            go.Scatter(
                x=growth_years, y=growth_values, mode="lines+markers", name="predicted"
            )
        ],
        layout=go.Layout(title_text="Demo: Growth (predicted population)"),
    )

    hours = list(range(24))
    energy_curve = [
        5.0 if h < 6 else 8.0 if h < 9 else 6.5 if h < 16 else 9.5 if h < 20 else 6.0
        for h in hours
    ]
    fig_energy = go.Figure(
        data=[
            go.Scatter(
                x=hours, y=energy_curve, mode="lines+markers", name="demand (MWh)"
            )
        ],
        layout=go.Layout(title_text="Demo: Energy (daily profile)"),
    )

    traffic_curve = [
        (
            150
            if h < 6
            else (
                850 if h in (7, 8) else 400 if h < 16 else 900 if h in (17, 18) else 200
            )
        )
        for h in hours
    ]
    fig_traffic = go.Figure(
        data=[
            go.Scatter(x=hours, y=traffic_curve, mode="lines+markers", name="volume")
        ],
        layout=go.Layout(title_text="Demo: Traffic (daily profile)"),
    )

    navbar = dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand("SUSPS", href="#"),
                dbc.Nav(
                    [
                        dbc.NavItem(
                            dbc.NavLink("Dashboard", href=requests_pathname_prefix)
                        ),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
            ]
        ),
        color="dark",
        dark=True,
        className="mb-4",
    )

    app.layout = dbc.Container(
        [
            navbar,
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Controls"),
                                    dbc.CardBody(
                                        [
                                            html.P("Data source for demo charts"),
                                            dcc.RadioItems(
                                                id="data-source",
                                                options=[
                                                    {
                                                        "label": "Demo (local)",
                                                        "value": "demo",
                                                    },
                                                    {"label": "API", "value": "api"},
                                                ],
                                                value="demo",
                                                inline=True,
                                            ),
                                            html.Hr(),
                                            html.P(
                                                "Smart Urban Simulation and Prediction System"
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dcc.Graph(id="readiness-graph", figure=fig_readiness),
                            dcc.Graph(id="growth-graph", figure=fig_growth),
                            dcc.Graph(id="energy-graph", figure=fig_energy),
                            dcc.Graph(id="traffic-graph", figure=fig_traffic),
                        ],
                        width=9,
                    ),
                ]
            ),
        ],
        fluid=True,
    )

    @app.callback(
        Output("growth-graph", "figure"),
        Output("energy-graph", "figure"),
        Output("traffic-graph", "figure"),
        Input("data-source", "value"),
    )
    def _update_figs(source: str):
        base = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

        def _fig_growth(items):
            years = [it["year"] for it in items]
            values = [it["predicted_population"] for it in items]
            return go.Figure(
                data=[
                    go.Scatter(
                        x=years, y=values, mode="lines+markers", name="predicted"
                    )
                ],
                layout=go.Layout(title_text="Demo: Growth (predicted population)"),
            )

        def _fig_energy(items):
            hours = [it["hour"] for it in items]
            vals = [it["demand_mwh"] for it in items]
            return go.Figure(
                data=[
                    go.Scatter(
                        x=hours, y=vals, mode="lines+markers", name="demand (MWh)"
                    )
                ],
                layout=go.Layout(title_text="Demo: Energy (daily profile)"),
            )

        def _fig_traffic(items):
            hours = [it["hour"] for it in items]
            vals = [it["volume"] for it in items]
            return go.Figure(
                data=[go.Scatter(x=hours, y=vals, mode="lines+markers", name="volume")],
                layout=go.Layout(title_text="Demo: Traffic (daily profile)"),
            )

        if source == "api":
            try:
                g = requests.get(f"{base}/growth", timeout=5).json().get("items", [])
                e = requests.get(f"{base}/energy", timeout=5).json().get("items", [])
                t = requests.get(f"{base}/traffic", timeout=5).json().get("items", [])
                return _fig_growth(g), _fig_energy(e), _fig_traffic(t)
            except Exception:
                pass  # fall back to demo

        # demo fallback
        g = _predict_growth()
        e = _energy_profile()
        t = _traffic_profile()
        return _fig_growth(g), _fig_energy(e), _fig_traffic(t)

    return app
