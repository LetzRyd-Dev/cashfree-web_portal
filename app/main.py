import os
from pathlib import Path
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, get_db
from app.api.auth import router as auth_router
from app.api.drivers import router as drivers_router
from app.api.operators import router as operators_router
from app.api.hisaabs import router as hisaabs_router
from app.api.payments import router as payments_router, create_cashfree_order, cashfree_webhook
from app.api.tickets import router as tickets_router
from app.api.notifications import router as notifications_router
from app.api.referrals import router as referrals_router
from app.api.audit import router as audit_router
from app.schemas.app_schemas import CreateOrderRequest, CreateOrderResponse

# In production: disable Swagger UI (/docs), ReDoc (/redoc), and OpenAPI schema (/openapi.json)
# to prevent API enumeration by malicious actors.
_is_production = settings.ENVIRONMENT.lower() == "production"
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Complete Backend API for LetzRyd Partner App (Drivers, Operators, Hisaabs, Payments, Tickets, Notifications, Referrals, Audit Logs)",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

# CORS Setup
# Production: restrict to the official LetzRyd portal origin only.
# Development/Sandbox: allow all origins for easy local/preview testing.
_PROD_ORIGINS = [
    "https://letzryd-portal-925756819101.asia-south1.run.app",
    "https://letzryd.com",
    "https://www.letzryd.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_PROD_ORIGINS if _is_production else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Create database tables automatically on startup
@app.on_event("startup")
def startup_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] PostgreSQL database tables verified/created successfully!")
    except Exception as e:
        print(f"[WARN] Database connection notice during startup: {e}")

# Include Routers under /api
api_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=api_prefix)
app.include_router(drivers_router, prefix=api_prefix)
app.include_router(operators_router, prefix=api_prefix)
app.include_router(hisaabs_router, prefix=api_prefix)
app.include_router(payments_router, prefix=api_prefix)
app.include_router(tickets_router, prefix=api_prefix)
app.include_router(notifications_router, prefix=api_prefix)
app.include_router(referrals_router, prefix=api_prefix)
app.include_router(audit_router, prefix=api_prefix)

# Direct root endpoint alias for Cashfree checkout
@app.post("/api/create-order", response_model=CreateOrderResponse, tags=["Payments & Cashfree"])
def root_create_order(req: CreateOrderRequest, request: Request, db: Session = Depends(get_db)):
    return create_cashfree_order(req, request, db)

# Direct root webhook aliases for Cashfree
@app.post("/api/webhook", tags=["Payments & Cashfree"])
@app.post("/api/webhook/cashfree", tags=["Payments & Cashfree"])
@app.post("/api/payments/webhook", tags=["Payments & Cashfree"])
@app.post("/payments/webhook", tags=["Payments & Cashfree"])
async def root_cashfree_webhook(request: Request, db: Session = Depends(get_db)):
    return await cashfree_webhook(request, db)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": settings.DB_HOST,
        "cashfree_mode": "production" if settings.CASHFREE_ENV.upper() == "PRODUCTION" else "sandbox"
    }

@app.get("/api/config")
def get_app_config():
    return {
        "cashfree_mode": "production" if settings.CASHFREE_ENV.upper() == "PRODUCTION" else "sandbox",
        "cashfree_env": settings.CASHFREE_ENV.upper()
    }

# Mount static frontend production assets if dist/ exists
dist_path = Path(__file__).resolve().parent.parent / "dist"
if dist_path.is_dir():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

