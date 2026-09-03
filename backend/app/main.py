from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .schemas.health import HealthResponse
from .api.reconciliation import router as reconciliation_router
from .api.evaluation import router as evaluation_router

app = FastAPI(
    title="Thrive Treasury AI Backend",
    description="Financial reconciliation and exception-intelligence backend foundation for the Razorpay AI Buildathon.",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration for local frontend development (http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
   allow_origins=[
    "http://localhost:5173",
    "https://thrive-treasury-ai-front.onrender.com",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers under configured prefix (/api)
app.include_router(reconciliation_router, prefix=settings.api_prefix)
app.include_router(evaluation_router, prefix=settings.api_prefix)


@app.get(
    f"{settings.api_prefix}/health",
    response_model=HealthResponse,
    summary="Health Check",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """Returns basic system liveness confirmation."""
    return HealthResponse(
        status="ok",
        service="thrive-treasury-ai",
        version=settings.version,
    )
