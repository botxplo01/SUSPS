from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse

from src.webapp.app import create_dash_app

app = FastAPI(title="SUSPS Backend", version="0.1.0")

# CORS (adjust origins as needed for deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return JSONResponse({"status": "ok", "service": "susps", "version": "0.1.0"})


@app.get("/growth")
def demo_growth():
    base = 800_000
    years = list(range(2025, 2031))
    # Simple +3% growth per year
    items = [
        {"year": y, "predicted_population": int(base * (1.03 ** (y - years[0])))}
        for y in years
    ]
    return {"items": items}


@app.get("/energy")
def demo_energy():
    # Simple daily curve
    hours = list(range(24))
    curve = [
        5.0 if h < 6 else 8.0 if h < 9 else 6.5 if h < 16 else 9.5 if h < 20 else 6.0
        for h in hours
    ]
    items = [{"hour": h, "demand_mwh": v} for h, v in zip(hours, curve)]
    return {"items": items}


@app.get("/traffic")
def demo_traffic():
    hours = list(range(24))
    curve = [
        (
            150
            if h < 6
            else (
                850 if h in (7, 8) else 400 if h < 16 else 900 if h in (17, 18) else 200
            )
        )
        for h in hours
    ]
    items = [{"hour": h, "volume": v} for h, v in zip(hours, curve)]
    return {"items": items}


# Redirect root to dashboard so primary URL works on Render
@app.get("/")
def root_redirect():
    return RedirectResponse(url="/dash/")


# Mount Dash app under /dash
_dash_app = create_dash_app(requests_pathname_prefix="/dash/")
app.mount("/dash", WSGIMiddleware(_dash_app.server))
