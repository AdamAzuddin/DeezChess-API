from fastapi import FastAPI
from app.routes import api

app = FastAPI()

# Include route(s)
app.include_router(api.router)
