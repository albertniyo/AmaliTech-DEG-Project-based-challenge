from fastapi import FastAPI
import asyncio
import time
from monitors import router as monitors_router, countdown
from store import store

app = FastAPI(title="Pulse-Check API")
app.include_router(monitors_router)

@app.on_event("startup")
async def resume_monitors():
    """Restart countdowns for all monitors that were active before shutdown."""
    all_monitors = await store.get_all()
    active_count = 0
    for mon in all_monitors:
        if mon["status"] == "active":
            now = time.monotonic()
            await store.set_timer_start(mon["id"], now)
            task = asyncio.create_task(countdown(mon["id"], mon["timeout"]))
            store.set_task(mon["id"], task)
            active_count += 1
    print(f"Resumed {active_count} active monitors")

@app.get("/")
def root():
    return {"message": "Pulse-Check API running"}

if __name__== "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)