from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router

app = FastAPI(
    title="Patient AI Appointment Reminder System",
    description="A foundational API for triggering and auditing patient AI calls.",
    version="1.0.0"
)

# ─── CORS CONFIGURATION ──────────────────────────────────────────────────
# This allows your frontend (when you build it) to securely communicate with this API.
# You can update the origins list later if your frontend runs on a specific port (e.g., http://localhost:5173 for Vite)
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",  # Common frontend ports
    "*"                       # Revert to this temporarily during development if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

# ─── ROUTER REGISTRATION ─────────────────────────────────────────────────
app.include_router(api_router)

@app.get("/", tags=["health"])
async def root():
    """
    Health check endpoint to verify the API is up and running.
    """
    return {
        "status": "healthy",
        "message": "Welcome to the Patient Call Foundation API"
    }