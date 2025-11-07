from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse

from src.models.growth import predict_growth
from src.models.energy import daily_profile as energy_profile
from src.models.traffic import daily_profile as traffic_profile
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
    items = predict_growth()
    return {"items": items}


@app.get("/energy")
def demo_energy():
    items = energy_profile()
    return {"items": items}


@app.get("/traffic")
def demo_traffic():
    items = traffic_profile()
    return {"items": items}


# Redirect root to dashboard so primary URL works on Render
@app.get("/")
def root_redirect():
    return RedirectResponse(url="/dash/")


# Mount Dash app under /dash
_dash_app = create_dash_app(requests_pathname_prefix="/dash/")
app.mount("/dash", WSGIMiddleware(_dash_app.server))
