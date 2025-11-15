from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import os
import requests


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


def _empty_fig(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title_text=title)
    return fig


def _make_figures():
    """Return initial empty figures for readiness, growth, energy, traffic.

    These are placeholders; real data is only loaded after an area is selected.
    """
    fig_readiness = _empty_fig("Module readiness")
    fig_growth = _empty_fig("Growth (select an area)")
    fig_energy = _empty_fig("Energy (select an area)")
    fig_traffic = _empty_fig("Traffic (select an area)")
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
                html.P("Select area", className="text-secondary small"),
                dcc.Dropdown(
                    id="area-select",
                    options=[],
                    placeholder="Search or select area...",
                    style={"marginBottom": "0.75rem"},
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
                    [
                        dbc.Col(
                            dcc.Graph(id="traffic-graph", figure=fig_traffic), md=6
                        ),
                        dbc.Col(dcc.Graph(id="energy-summary-graph"), md=6),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id="traffic-summary-graph"), md=12),
                    ]
                ),
                html.Hr(),
                html.H4("Insights"),
                html.Div(
                    id="insights-panel", children=html.Em("Generating insights...")
                ),
            ]
        )

    def _growth_content():
        return html.Div(
            [
                html.H3("Growth"),
                html.P("Projected population by year."),
                dcc.Graph(id="growth-graph", figure=fig_growth),
                # Hidden graphs to satisfy callbacks on this route
                html.Div(
                    [
                        dcc.Graph(id="energy-graph", style={"display": "none"}),
                        dcc.Graph(id="traffic-graph", style={"display": "none"}),
                        dcc.Graph(id="energy-summary-graph", style={"display": "none"}),
                        dcc.Graph(
                            id="traffic-summary-graph", style={"display": "none"}
                        ),
                    ],
                    style={"display": "none"},
                ),
                html.Hr(),
                html.H4("Insights"),
                html.Div(
                    id="insights-panel", children=html.Em("Generating insights...")
                ),
            ]
        )

    def _energy_content():
        return html.Div(
            [
                html.H3("Energy"),
                html.P("Daily energy demand (predicted vs actual when available)."),
                dcc.Graph(id="energy-graph", figure=fig_energy),
                html.Hr(),
                html.P("Energy summary"),
                dcc.Graph(id="energy-summary-graph"),
                # Hidden graphs to satisfy callbacks on this route
                html.Div(
                    [
                        dcc.Graph(id="growth-graph", style={"display": "none"}),
                        dcc.Graph(id="traffic-graph", style={"display": "none"}),
                        dcc.Graph(
                            id="traffic-summary-graph", style={"display": "none"}
                        ),
                    ],
                    style={"display": "none"},
                ),
                html.Hr(),
                html.H4("Insights"),
                html.Div(
                    id="insights-panel", children=html.Em("Generating insights...")
                ),
            ]
        )

    def _traffic_content():
        return html.Div(
            [
                html.H3("Traffic"),
                html.P("Hourly traffic volume (predicted vs actual when available)."),
                dcc.Graph(id="traffic-graph", figure=fig_traffic),
                html.Hr(),
                html.P("Traffic hourly summary"),
                dcc.Graph(id="traffic-summary-graph"),
                # Hidden graphs to satisfy callbacks on this route
                html.Div(
                    [
                        dcc.Graph(id="growth-graph", style={"display": "none"}),
                        dcc.Graph(id="energy-graph", style={"display": "none"}),
                        dcc.Graph(id="energy-summary-graph", style={"display": "none"}),
                    ],
                    style={"display": "none"},
                ),
                html.Hr(),
                html.H4("Insights"),
                html.Div(
                    id="insights-panel", children=html.Em("Generating insights...")
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

    # Load area options from /areas for the sidebar dropdown
    @app.callback(
        Output("area-select", "options"),
        Input("url", "pathname"),
        prevent_initial_call=False,
    )
    def _load_area_options(_pathname: str):
        base = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
        try:
            r = requests.get(f"{base}/areas", timeout=8)
            r.raise_for_status()
            items = r.json().get("items", [])
        except Exception:
            items = []
        options = [
            {
                "label": f"{it.get('name', 'Area')} ({it.get('area_type', '')})",
                "value": it.get("area_id") or it.get("id"),
            }
            for it in items
        ]
        return options

    # Figures update based on selected area (no demo toggle)
    @app.callback(
        Output("growth-graph", "figure"),
        Output("energy-graph", "figure"),
        Output("traffic-graph", "figure"),
        Output("energy-summary-graph", "figure"),
        Output("traffic-summary-graph", "figure"),
        Input("area-select", "value"),
    )
    def _update_figs(area_id):
        base = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

        def _fig_growth(items):
            if not items:
                return _empty_fig("Growth (no data for selected area)")
            years = [it.get("year") for it in items]
            values = [it.get("predicted_population") for it in items]
            return go.Figure(
                data=[
                    go.Scatter(
                        x=years, y=values, mode="lines+markers", name="predicted"
                    )
                ],
                layout=go.Layout(title_text="Growth (predicted population)"),
            )

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
            # DB shape: items with ts, predicted, actual
            if items and ("predicted" in items[0] or "actual" in items[0]):
                xs = [it.get("ts") for it in items]
                pred = [it.get("predicted") for it in items]
                act = [it.get("actual") for it in items]
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(x=xs, y=pred, mode="lines+markers", name="predicted")
                )
                fig.add_trace(
                    go.Scatter(x=xs, y=act, mode="lines+markers", name="actual")
                )
                fig.update_layout(title_text="Energy: predicted vs actual")
                return fig
            # Processed/demo shape: hour + demand_mwh
            hours = [it.get("hour") for it in items]
            vals = [it.get("demand_mwh") for it in items]
            return go.Figure(
                data=[
                    go.Scatter(
                        x=hours, y=vals, mode="lines+markers", name="demand (MWh)"
                    )
                ],
                layout=go.Layout(title_text="Energy: daily profile"),
            )

        def _fig_traffic(items):
            # DB shape: items with ts, predicted_volume, actual_volume
            if items and (
                "predicted_volume" in items[0] or "actual_volume" in items[0]
            ):
                xs = [it.get("ts") for it in items]
                pred = [it.get("predicted_volume") for it in items]
                act = [it.get("actual_volume") for it in items]
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(x=xs, y=pred, mode="lines+markers", name="predicted")
                )
                fig.add_trace(
                    go.Scatter(x=xs, y=act, mode="lines+markers", name="actual")
                )
                fig.update_layout(title_text="Traffic: predicted vs actual")
                return fig
            # Processed/demo shape: hour + volume
            hours = [it.get("hour") for it in items]
            vals = [it.get("volume") for it in items]
            return go.Figure(
                data=[go.Scatter(x=hours, y=vals, mode="lines+markers", name="volume")],
                layout=go.Layout(title_text="Traffic: daily profile"),
            )

        def _fig_energy_summary(items):
            # DB shape: area_name + predicted/actual averages
            if items and "area_name" in items[0]:
                x = [str(it.get("area_name")) for it in items]
                pred = [float(it.get("predicted", 0) or 0) for it in items]
                act = [float(it.get("actual", 0) or 0) for it in items]
                fig = go.Figure()
                fig.add_trace(go.Bar(x=x, y=pred, name="predicted"))
                fig.add_trace(go.Bar(x=x, y=act, name="actual"))
                fig.update_layout(barmode="group", title_text="Energy summary by area")
                return fig
            # Processed shape: sector + demand_mwh
            sectors = [str(it.get("sector", "")) for it in items]
            values = [float(it.get("demand_mwh", it.get("pct", 0))) for it in items]
            return go.Figure(
                data=[go.Bar(x=sectors, y=values, name="sector demand")],
                layout=go.Layout(title_text="Energy sector summary"),
            )

        def _fig_traffic_hourly(items):
            # DB shape: area_name + predicted/actual volume averages (not hourly) — show by area
            if (
                items
                and "area_name" in items[0]
                and ("predicted_volume" in items[0] or "actual_volume" in items[0])
            ):
                x = [str(it.get("area_name")) for it in items]
                pred = [float(it.get("predicted_volume", 0) or 0) for it in items]
                act = [float(it.get("actual_volume", 0) or 0) for it in items]
                fig = go.Figure()
                fig.add_trace(go.Bar(x=x, y=pred, name="predicted"))
                fig.add_trace(go.Bar(x=x, y=act, name="actual"))
                fig.update_layout(barmode="group", title_text="Traffic summary by area")
                return fig
            # Processed shape: hourly averages
            hours = [int(it.get("hour", it.get("hourly", 0))) for it in items]
            vals = [
                float(it.get("avg_veh_per_hour", it.get("volume", 0))) for it in items
            ]
            return go.Figure(
                data=[go.Bar(x=hours, y=vals, name="avg veh/h")],
                layout=go.Layout(title_text="Traffic average hourly volume"),
            )

        # No area selected: keep empty figures with descriptive titles
        if area_id is None:
            return (
                _empty_fig("Growth (select an area)"),
                _empty_fig("Energy (select an area)"),
                _empty_fig("Traffic (select an area)"),
                _empty_fig("Energy summary (select an area)"),
                _empty_fig("Traffic summary (select an area)"),
            )

        # Load data from API only (no demo fallback)
        params = f"?area_id={area_id}" if area_id is not None else ""
        try:
            g = (
                requests.get(f"{base}/growth{params}", timeout=8)
                .json()
                .get("items", [])
            )
            e = (
                requests.get(f"{base}/energy{params}", timeout=8)
                .json()
                .get("items", [])
            )
            t = (
                requests.get(f"{base}/traffic{params}", timeout=8)
                .json()
                .get("items", [])
            )
            es = (
                requests.get(f"{base}/energy/summary{params}", timeout=8)
                .json()
                .get("items", [])
            )
            ts = (
                requests.get(f"{base}/traffic/summary{params}", timeout=8)
                .json()
                .get("items", [])
            )
        except Exception:
            return (
                _empty_fig("Growth (error loading data)"),
                _empty_fig("Energy (error loading data)"),
                _empty_fig("Traffic (error loading data)"),
                _empty_fig("Energy summary (error loading data)"),
                _empty_fig("Traffic summary (error loading data)"),
            )

        return (
            _fig_growth(g),
            _fig_energy(e),
            _fig_traffic(t),
            _fig_energy_summary(es),
            _fig_traffic_hourly(ts),
        )

    # Insights updater (area-gated)
    @app.callback(
        Output("insights-panel", "children"),
        Input("area-select", "value"),
        Input("url", "pathname"),
        prevent_initial_call=False,
    )
    def _update_insights(area_id, pathname: str):
        # No area selected: show descriptive text only
        if area_id is None:
            text = (
                "Select an area from the sidebar to load data and generate "
                "AI advisory for this page. The advisory engine summarises "
                "recent growth, energy, and traffic patterns for the chosen "
                "area using the available datasets, APIs, and models."
            )
            return html.Div(
                [
                    dcc.Markdown(text),
                ]
            )
        base = os.getenv("API_BASE_URL", "").strip()
        alt = os.getenv("API_BASE_URL_ALT", "").strip()
        # Build candidate list: env bases then common locals
        candidates = [
            b
            for b in [base, alt, "http://127.0.0.1:8001", "http://127.0.0.1:8000"]
            if b
        ]
        # Deduplicate while preserving order
        seen = set()
        candidates = [b for b in candidates if not (b in seen or seen.add(b))]

        prefix = (requests_pathname_prefix or "/").rstrip("/") + "/"
        scope = "dashboard"
        if (pathname or "").startswith(f"{prefix}growth"):
            scope = "growth"
        elif (pathname or "").startswith(f"{prefix}energy"):
            scope = "energy"
        elif (pathname or "").startswith(f"{prefix}traffic"):
            scope = "traffic"

        def _fetch(api_base: str):
            try:
                tmo = int(os.getenv("HF_TIMEOUT", "30") or 30)
            except Exception:
                tmo = 30
            try:
                params = {"zone_id": str(area_id)} if area_id is not None else None
                r = requests.get(
                    f"{api_base}/advisory/{scope}",
                    params=params,
                    timeout=max(15, tmo),
                )
                r.raise_for_status()
                return r.json()  # type: ignore[no-any-return]
            except Exception:
                return None

        # Try candidates until we get non-fallback
        used_base = candidates[0] if candidates else "http://127.0.0.1:8000"
        res = None
        first_fallback = None
        for b in candidates or ["http://127.0.0.1:8000"]:
            r = _fetch(b)
            if not r:
                continue
            if not bool(r.get("fallback", False)):
                res = r
                used_base = b
                break
            if first_fallback is None:
                first_fallback = r
        if res is None and first_fallback is not None:
            res = first_fallback

        # default values so we always define these
        fallback = False
        footer = ""
        if res:
            text = res.get("insights") or "No insights available."
            model = res.get("model") or ""
            cached = res.get("cached")
            when = res.get("generated_at") or ""
            fallback = bool(res.get("fallback", False))
            if model or when:
                state = "fallback" if fallback else ("cached" if cached else "fresh")
                footer = f"Generated by {model} • {state} • {when} • API: {used_base}"
        else:
            text = "Advisory currently unavailable. Ensure the backend is reachable and HUGGINGFACE_API_KEY is set."

        banner = (
            html.Div(
                (
                    "Model unavailable — showing fallback advisory"
                    if fallback and used_base
                    else "Switching API base for insights"
                ),
                className="text-warning small",
                style={"marginBottom": "0.25rem"},
            )
            if fallback or (used_base != (base or "http://127.0.0.1:8000"))
            else html.Span()
        )
        return html.Div(
            [
                banner,
                dcc.Markdown(text),
                (
                    html.Div(
                        footer,
                        className="text-muted small",
                        style={"marginTop": "0.5rem"},
                    )
                    if footer
                    else html.Span()
                ),
            ]
        )

    return app

    return app
