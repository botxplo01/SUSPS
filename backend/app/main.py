from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from a2wsgi import WSGIMiddleware

from .api.routes import router as api_router
from .dash_app import create_dash_app

app = FastAPI(title="SUSPS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router)

# Mount Dash under /dash
_dash = create_dash_app("/dash/")
# a2wsgi.WSGIMiddleware is a valid ASGI app; ignore type to satisfy mypy
app.mount("/dash", WSGIMiddleware(_dash.server))  # type: ignore[arg-type]
