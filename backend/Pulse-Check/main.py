from fastapi import FastAPI
import asyncio
from monitors import router as monitors_router, countdown
from store import store

app = FastAPI(title="Pulse-Check API")
app.include_router(monitors_router)

@app.get("/")
def root():
    return {"message": "Pulse-Check API running"}
