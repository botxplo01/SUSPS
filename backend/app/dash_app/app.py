from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from sqlalchemy import text

from ..core.db import engine


def _energy_summary():
    """Return (area_names, predicted_avgs, actual_avgs) using SQL only."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT ua.name as area_name,
                       AVG(e.predicted_demand) AS predicted,
                       AVG(e.actual_demand)    AS actual
                FROM energy_consumption e
                JOIN urban_areas ua ON ua.area_id = e.area_id
                GROUP BY ua.name
                ORDER BY MIN(ua.area_id)
                """
            )
        ).all()
    area_names = [str(r[0]) for r in rows]
    predicted = [float(r[1]) if r[1] is not None else 0.0 for r in rows]
    actual = [float(r[2]) if r[2] is not None else 0.0 for r in rows]
    return area_names, predicted, actual


def _traffic_summary():
    """Return (area_names, predicted_avgs, actual_avgs) using SQL only."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT ua.name as area_name,
                       AVG(t.predicted_volume) AS predicted,
                       AVG(t.actual_volume)    AS actual
                FROM traffic_flow t
                JOIN urban_areas ua ON ua.area_id = t.area_id
                GROUP BY ua.name
                ORDER BY MIN(ua.area_id)
                """
            )
        ).all()
    area_names = [str(r[0]) for r in rows]
    predicted = [int(r[1]) if r[1] is not None else 0 for r in rows]
    actual = [int(r[2]) if r[2] is not None else 0 for r in rows]
    return area_names, predicted, actual


def _bar_figure(x, y_series, names, title, y_title):
    # Build a Plotly figure spec as a plain dict to avoid requiring plotly Python package
    def _fmt(v):
        try:
            # format floats to 1 decimal, ints as int
            if isinstance(v, (int,)):
                return f"{v}"
            fv = float(v)
            return f"{fv:.1f}"
        except Exception:
            return str(v)

    data = []
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    for i, ys in enumerate(y_series):
        data.append(
            {
                "type": "bar",
                "x": x,
                "y": ys,
                "name": names[i],
                "marker": {"color": colors[i % len(colors)]},
                "text": [_fmt(v) for v in ys],
                "textposition": "auto",
                "hovertemplate": "%{x}<br>%{fullData.name}: %{y}<extra></extra>",
            }
        )
    layout = {
        "barmode": "group",
        "title": {"text": title},
        "margin": {"l": 50, "r": 20, "t": 50, "b": 50},
        "legend": {"orientation": "h", "title": {"text": "Series"}},
        "xaxis": {"title": {"text": "Area"}},
        "yaxis": {"title": {"text": y_title}},
    }
    return {"data": data, "layout": layout}


def create_dash_app(requests_pathname_prefix: str = "/dash/") -> Dash:
    external_stylesheets = [dbc.themes.BOOTSTRAP]

    dash_app = Dash(
        __name__,
        requests_pathname_prefix=requests_pathname_prefix,
        external_stylesheets=external_stylesheets,
        suppress_callback_exceptions=True,
    )

    # Prepare figures (handle empty DB gracefully)
    try:
        e_x, e_pred, e_act = _energy_summary()
    except Exception:
        e_x, e_pred, e_act = [], [], []
    try:
        t_x, t_pred, t_act = _traffic_summary()
    except Exception:
        t_x, t_pred, t_act = [], [], []

    energy_fig = _bar_figure(
        e_x,
        [e_pred, e_act],
        ["predicted", "actual"],
        "Energy by Area (avg)",
        "Avg demand",
    )
    traffic_fig = _bar_figure(
        t_x,
        [t_pred, t_act],
        ["predicted", "actual"],
        "Traffic by Area (avg)",
        "Avg volume",
    )

    status_alert = dbc.Alert(
        (
            "Connected to DB and loaded summaries."
            if e_x or t_x
            else "No data yet. Seed the DB to view charts."
        ),
        color="success" if e_x or t_x else "warning",
    )

    dash_app.layout = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(html.H2("SUSPS Dashboard"), width=6),
                    dbc.Col(
                        dbc.Nav(
                            [
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Dashboard Home", href=requests_pathname_prefix
                                    )
                                ),
                                dbc.NavItem(dbc.NavLink("API Health", href="/health")),
                            ],
                            pills=True,
                            className="justify-content-end",
                        ),
                        width=6,
                    ),
                ],
                align="center",
                className="my-2",
            ),
            status_alert,
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=energy_fig), md=6),
                    dbc.Col(dcc.Graph(figure=traffic_fig), md=6),
                ],
                className="my-3",
            ),
        ],
        fluid=True,
    )

    return dash_app
