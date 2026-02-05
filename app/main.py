"""
FastAPI application main entry point.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import auth_router
from app.core.database import Base, engine


# Create FastAPI application with enhanced Swagger configuration
app = FastAPI(
    title="FwdStar Auth API",
    description="""
    ## 🚀 Production-grade authentication system for B2B freight marketplace

    ### Features
    - JWT Authentication with httpOnly cookies
    - Role-Based Access Control (RBAC)
    - Comprehensive audit logging
    - Brute force protection
    - XSS and CSRF protection

    ### Security
    All endpoints are secured with industry-standard security practices including:
    - Secure password hashing (bcrypt)
    - Account lockout after failed attempts
    - Token refresh mechanism
    - Audit trail for all actions
    """,
    version="1.0.0",
    contact={
        "name": "FwdStar API Support",
        "email": "support@fwdstar.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT == "development" else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Include API routes
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT
    }


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint.
    """
    return {
        "message": "FwdStar Authentication API",
        "version": "1.0.0",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else None
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=10000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )
