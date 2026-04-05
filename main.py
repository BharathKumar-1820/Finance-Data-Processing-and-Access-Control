from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from db import engine, Base, async_session, init_db
from routers import users, financial_records, dashboard
from utils.exceptions import NotFoundError, UnauthorizedError, ValidationError
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup startup/shutdown events
async def startup():
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifespan"""
    await startup()
    yield

# Create FastAPI app
app = FastAPI(
    title="Finance Data Processing and Access Control",
    description="Backend for finance dashboard with role-based access control",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(financial_records.router, prefix="/api", tags=["financial_records"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])

# Exception handlers
@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request, exc: NotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(UnauthorizedError)
async def unauthorized_exception_handler(request, exc: UnauthorizedError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        error_detail = {
            "type": error.get("type", "unknown"),
            "loc": error.get("loc", []),
            "msg": error.get("msg", "Validation error"),
        }
        errors.append(error_detail)
    
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": errors}
    )

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Finance Data Processing and Access Control",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}