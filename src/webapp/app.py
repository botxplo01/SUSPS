from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import os
import requests

from src.models.growth import predict_growth as _predict_growth
from src.models.energy import daily_profile as _energy_profile
from src.models.traffic import daily_profile as _traffic_profile


def _placeholder_map(el_id: str, title: str) -> html.Div:
    return html.Div(
        [
            html.Div(
                title,
                className="text-muted",
                style={"position": "absolute", "top": "8px", "left": "12px"},
            ),
            html.Span("Map area", className="text-secondary"),
        ],
        id=el_id,
        style={
            "height": "320px",
            "backgroundColor": "#e9ecef",
            "border": "1px dashed #adb5bd",
            "borderRadius": "4px",
            "position": "relative",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
        },
    )


def _placeholder_table(title: str) -> html.Div:
    header = html.Thead(
        html.Tr([html.Th("Column A"), html.Th("Column B"), html.Th("Column C")])
    )
    rows = [
        html.Tr([html.Td("A1"), html.Td("B1"), html.Td("C1")]),
        html.Tr([html.Td("A2"), html.Td("B2"), html.Td("C2")]),
        html.Tr([html.Td("A3"), html.Td("B3"), html.Td("C3")]),
    ]
    table = dbc.Table([header, html.Tbody(rows)], bordered=True, hover=True, size="sm")
    return html.Div([html.Div(title, className="text-muted mb-2"), table])


def _make_figures():
    """Return initial placeholder figures for readiness, growth, energy, traffic."""
    # Readiness chart (placeholder progress)
    modules = ["Growth", "Energy", "Traffic"]
    readiness = [10, 5, 2]
    fig_readiness = go.Figure(
        data=[go.Bar(x=modules, y=readiness, marker_color="#1f77b4")],
        layout=go.Layout(title_text="Initial Module Readiness (placeholder)"),
    )

    # Growth (demo)
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

    # Energy (demo)
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

    # Traffic (demo)
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
    return fig_readiness, fig_growth, fig_energy, fig_traffic


def create_dash_app(requests_pathname_prefix: str = "/") -> Dash:
    # External stylesheets
    external_stylesheets = [dbc.themes.BOOTSTRAP]

    assets_path = os.path.join(os.path.dirname(__file__), "assets")
    app = Dash(
        __name__,
        requests_pathname_prefix=requests_pathname_prefix,
        external_stylesheets=external_stylesheets,
        suppress_callback_exceptions=True,
        title="SUSPS Dashboard",
        assets_folder=assets_path,
    )

    fig_readiness, fig_growth, fig_energy, fig_traffic = _make_figures()

    # Sidebar builder
    def _sidebar(prefix: str) -> html.Div:
        return html.Div(
            [
                html.H2("SUSPS", className="display-6 mb-3"),
                html.Hr(),
                html.P("Data source for demo charts", className="text-secondary small"),
                dcc.RadioItems(
                    id="data-source",
                    options=[
                        {"label": "Demo (local)", "value": "demo"},
                        {"label": "API", "value": "api"},
                    ],
                    value=os.getenv("DEFAULT_DATA_SOURCE", "demo"),
                    style={"marginBottom": "0.5rem"},
                ),
                html.Hr(),
                dbc.Nav(
                    [
                        dbc.NavLink(
                            "Dashboard",
                            href=prefix,
                            id="nav-dashboard",
                            className="d-block w-100",
                        ),
                        dbc.NavLink(
                            "Growth",
                            href=f"{prefix}growth",
                            id="nav-growth",
                            className="d-block w-100",
                        ),
                        dbc.NavLink(
                            "Energy",
                            href=f"{prefix}energy",
                            id="nav-energy",
                            className="d-block w-100",
                        ),
                        dbc.NavLink(
                            "Traffic",
                            href=f"{prefix}traffic",
                            id="nav-traffic",
                            className="d-block w-100",
                        ),
                    ],
                    vertical=True,
                    pills=False,
                    className="mt-2",
                ),
            ],
            className="sidebar sidebar-fixed p-3 text-light",
            style={"backgroundColor": "#212529"},
        )

    # Content per route
    def _dashboard_content():
        return html.Div(
            [
                html.H3("Overview"),
                dcc.Graph(id="readiness-graph", figure=fig_readiness),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id="growth-graph", figure=fig_growth), md=6),
                        dbc.Col(dcc.Graph(id="energy-graph", figure=fig_energy), md=6),
                    ]
                ),
                dbc.Row(
                    [dbc.Col(dcc.Graph(id="traffic-graph", figure=fig_traffic), md=12)]
                ),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(
                            _placeholder_map("dashboard-map", "Map placeholder"), md=6
                        ),
                        dbc.Col(_placeholder_table("Table placeholder"), md=6),
                    ]
                ),
            ]
        )

    def _growth_content():
        return html.Div(
            [
                html.H3("Growth"),
                html.P("Projected population by year."),
                dcc.Graph(id="growth-graph", figure=fig_growth),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(_placeholder_map("growth-map", "Growth map"), md=6),
                        dbc.Col(_placeholder_table("Growth table"), md=6),
                    ]
                ),
            ]
        )

    def _energy_content():
        return html.Div(
            [
                html.H3("Energy"),
                html.P("Daily energy demand profile (MWh)."),
                dcc.Graph(id="energy-graph", figure=fig_energy),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(_placeholder_map("energy-map", "Energy map"), md=6),
                        dbc.Col(_placeholder_table("Energy table"), md=6),
                    ]
                ),
            ]
        )

    def _traffic_content():
        return html.Div(
            [
                html.H3("Traffic"),
                html.P("Hourly traffic volume profile."),
                dcc.Graph(id="traffic-graph", figure=fig_traffic),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(_placeholder_map("traffic-map", "Traffic map"), md=6),
                        dbc.Col(_placeholder_table("Traffic table"), md=6),
                    ]
                ),
            ]
        )

    def _render_content(pathname: str) -> html.Div:
        # Normalize by stripping the dash prefix so routes work under /dash/
        prefix = (requests_pathname_prefix or "/").rstrip("/") + "/"
        if pathname in (prefix, prefix.rstrip("/")):
            return _dashboard_content()
        if pathname.startswith(f"{prefix}growth"):
            return _growth_content()
        if pathname.startswith(f"{prefix}energy"):
            return _energy_content()
        if pathname.startswith(f"{prefix}traffic"):
            return _traffic_content()
        # Fallback
        return _dashboard_content()

    # Layout: fixed sidebar and content with left offset
    app.layout = html.Div(
        [
            dcc.Location(id="url"),
            _sidebar(requests_pathname_prefix),
            dbc.Container(
                html.Div(id="page-content", className="pt-5 px-4 content-offset"),
                fluid=True,
                className="p-0",
                style={"padding": 0},
            ),
        ]
    )

    # Activate nav item highlighting and render content
    @app.callback(
        Output("page-content", "children"),
        Output("nav-dashboard", "active"),
        Output("nav-growth", "active"),
        Output("nav-energy", "active"),
        Output("nav-traffic", "active"),
        Input("url", "pathname"),
        prevent_initial_call=False,
    )
    def _route(pathname: str):
        prefix = (requests_pathname_prefix or "/").rstrip("/") + "/"
        content = _render_content(pathname or prefix)
        active_dashboard = (pathname or prefix) == prefix
        active_growth = (pathname or "").startswith(f"{prefix}growth")
        active_energy = (pathname or "").startswith(f"{prefix}energy")
        active_traffic = (pathname or "").startswith(f"{prefix}traffic")
        return content, active_dashboard, active_growth, active_energy, active_traffic

    # Figures update based on data source toggle
    @app.callback(
        Output("growth-graph", "figure"),
        Output("energy-graph", "figure"),
        Output("traffic-graph", "figure"),
        Input("data-source", "value"),
        State("url", "pathname"),
    )
    def _update_figs(source: str, _pathname: str):
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
