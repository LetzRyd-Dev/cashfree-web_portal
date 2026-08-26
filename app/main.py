import os
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, get_db
from app.api.auth import router as auth_router
from app.api.drivers import router as drivers_router
from app.api.operators import router as operators_router
from app.api.hisaabs import router as hisaabs_router
from app.api.payments import router as payments_router, create_cashfree_order
from app.api.tickets import router as tickets_router
from app.api.notifications import router as notifications_router
from app.api.referrals import router as referrals_router
from app.api.audit import router as audit_router
from app.schemas.app_schemas import CreateOrderRequest, CreateOrderResponse

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Complete Backend API for LetzRyd Partner App (Drivers, Operators, Hisaabs, Payments, Tickets, Notifications, Referrals, Audit Logs)"
)

# CORS Setup - allows Vercel, Cloud Run, localhost, 127.0.0.1
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
def root_create_order(req: CreateOrderRequest, db: Session = Depends(get_db)):
    return create_cashfree_order(req, db)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": settings.DB_HOST
    }

# Mount static frontend production assets if dist/ exists
dist_path = Path(__file__).resolve().parent.parent / "dist"
if dist_path.is_dir():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)

