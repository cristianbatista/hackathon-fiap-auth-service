import uuid

from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.auth_router import router as auth_router
from src.api.health import router as health_router
from src.core.config import settings
from src.core.exceptions import http_exception_handler, unhandled_exception_handler
from src.core.logging import setup_logging

setup_logging(settings.log_level)

app = FastAPI(title="auth-service", version="0.1.0")

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    request.state.trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Trace-Id"] = request.state.trace_id
    return response


# Routers
app.include_router(auth_router)
app.include_router(health_router)


@app.get("/ping")
def ping() -> dict:
    return {"pong": True}
