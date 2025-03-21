from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import legal_moves
from app.api import healthcheck
from app.api import pgn_upload
from app.api import find_opening_move

app = FastAPI()

# ✅ Add CORS middleware BEFORE including any routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origin like ["http://localhost:5173"] if needed
    allow_credentials=True,
    allow_methods=["*"],  # Important: allows "OPTIONS" for WebGL
    allow_headers=["*"],  # Important: allows "Content-Type" etc.
)

# Include your routes AFTER CORS middleware
app.include_router(legal_moves.router)
app.include_router(healthcheck.router)
app.include_router(pgn_upload.router)
app.include_router(find_opening_move.router)