from fastapi import APIRouter, HTTPException, status
import asyncio
import time
from datetime import datetime, timezone
from models import MonitorCreate
from store import store

router = APIRouter(prefix="/monitors", tags=["monitors"])

# alert & status change
async def fire_alert(device_id: str):
    """Log alert and mark monitor as down."""
    await store.update_status(device_id, "down")
    alert = {
        "Alert": f"Device {device_id} is down!",
        "time": datetime.now(timezone.utc).isoformat()
    }
    print(alert)  # in real life, we can  send webhook or an email 


# countdown task
async def countdown(device_id: str, seconds: int):
    try:
        await asyncio.sleep(seconds)
        await fire_alert(device_id)
    except asyncio.CancelledError:
        # nothing to do
        pass


# endpoints
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_monitor(monitor: MonitorCreate):
    if await store.get(monitor.id):
        raise HTTPException(status_code=400, detail="monitor already exists")

    # create monitor in store
    mon = await store.create(monitor.id, monitor.timeout, monitor.alert_email)
    if not mon:
        raise HTTPException(status_code=500, detail="could not create monitor")

    # countdown starts and attach task
    now = time.monotonic()
    await store.set_timer_start(monitor.id, now)
    task = asyncio.create_task(countdown(monitor.id, monitor.timeout))
    store.set_task(monitor.id, task)

    return {"message": f"Monitor {monitor.id} registered", "id": monitor.id}


@router.post("/{device_id}/heartbeat")
async def heartbeat(device_id: str):
    mon = await store.get(device_id)
    if not mon:
        raise HTTPException(status_code=404, detail="Monitor not found")

    # cancel any running timer
    store.cancel_task(device_id)

    # if previously down, revive; if paused, unpause
    if mon["status"] in ("down", "paused"):
        await store.update_status(device_id, "active")

    # start a fresh timer
    now = time.monotonic()
    await store.set_timer_start(device_id, now)
    task = asyncio.create_task(countdown(device_id, mon["timeout"]))
    store.set_task(device_id, task)

    return {"message": f"Heartbeat received, timer reset for {device_id}"}


@router.post("/{device_id}/pause")
async def pause_monitor(device_id: str):
    mon = await store.get(device_id)
    if not mon:
        raise HTTPException(status_code=404, detail="Monitor not found")
    if mon["status"] != "active":
        raise HTTPException(status_code=400, detail=f"Monitor is {mon['status']}, cannot pause")

    store.cancel_task(device_id)
    await store.update_status(device_id, "paused")
    return {"message": f"Monitor {device_id} paused"}

@router.get("/{device_id}")
async def get_monitor(device_id: str):
    mon = await store.get(device_id)
    if not mon:
        raise HTTPException(status_code=404, detail="Monitor not found")

    # calculate remaining seconds when active
    remaining = None
    if mon["status"] == "active" and mon.get("timer_start"):
        elapsed = time.monotonic() - mon["timer_start"]
        remaining = max(0, mon["timeout"] - int(elapsed))

    return {
        "id": mon["id"],
        "timeout": mon["timeout"],
        "status": mon["status"],
        "alert_email": mon["alert_email"],
        "remaining_seconds": remaining
    }

@router.get("")
async def list_monitors():
    """Developer’s Choice: view all monitors."""
    all_monitors = await store.get_all()
    result = []
    for mon in all_monitors:
        remaining = None
        if mon["status"] == "active" and mon.get("timer_start"):
            elapsed = time.monotonic() - mon["timer_start"]
            remaining = max(0, mon["timeout"] - int(elapsed))
        result.append({
            "id": mon["id"],
            "timeout": mon["timeout"],
            "status": mon["status"],
            "alert_email": mon["alert_email"],
            "remaining_seconds": remaining
        })
    return result
    