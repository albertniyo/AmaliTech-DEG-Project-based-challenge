# Pulse-Check API
## The Problem and Solution

*CritMon* provides monitoring for remote solar farms and unmanned weather stations in areas with poor connectivity. These devices are supposed to send "I'm alive" signals every hour.

Currently, *CritMon* has no way of knowing if a device has gone offline (due to power failure or theft) until a human manually checks the logs. They need a system that alerts _them_ when a device _stops_ talking.

We propose a backend service solution that monitors remote devices using configurable countdown timers.
If a given device fails to send a heartbeat before its timer alerts, the system automatically fires an alert, build with **Python with FastAPI** using an in-memory state store with JSON file.

## Architecture Diagram
![Sequence Diagram](/backend/Pulse-Check/architecture_diagrams/sequence_d.png)

*The sequence diagram above shows the main interactions between the client, the API, and the background timer.*

![State Diagram](/backend/Pulse-Check/architecture_diagrams/state_d.png)

*State machine showing how a monitor transitions between Active, Paused, and Down based on heartbeats and timeouts.*

## Setup Instructions
### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### 1. Clone the repository
```bash
git clone https://github.com/albertniyo/AmaliTech-DEG-Project-based-challenge.git
cd backend/Pulse-Check
```

### 2. Install dependencies
```bash
uv sync
```

### 3. Start the server
```bash
# Using the built‑in __main__ block
uv run python main.py

# Or directly with uvicorn
uv run uvicorn main:app --reload
```

The API will be available at **http://localhost:8000**  and interactive Swagger docs at **http://localhost:8000/docs**.

## API Documentation

All endpoints are prefixed with `/monitors`.

### `POST /monitors` – Register a new monitor
**Request**
```json
{
  "id": "device001",
  "timeout": 60,
  "alert_email": "admin@critmon.com"
}
```
**Response** `201 Created`
```json
{
  "message": "Monitor device001 registered",
  "id": "device001"
}
```

### `POST /monitors/{id}/heartbeat` – Send a heartbeat
**Response** `200 OK`
```json
{
  "message": "Heartbeat received, timer reset for device001"
}
```
- If the device was `down`, it revives automatically.
- If the device was `paused`, it unpauses and restarts the timer.
- Returns `404` if the monitor does not exist.

### `POST /monitors/{id}/pause` – Pause monitoring
**Response** `200 OK`
```json
{
  "message": "Monitor device001 paused"
}
```
- Only works when the monitor is `active`.
- The timer is cancelled; no alert will fire.
- Sending a heartbeat automatically unpauses it.

### `GET /monitors` – List all monitors (Dashboard)
**Response** `200 OK`
```json
[
  {
    "id": "device001",
    "timeout": 60,
    "status": "active",
    "alert_email": "admin@critmon.com",
    "remaining_seconds": 42
  }
]
```
`remaining_seconds` shows the live countdown for active monitors, or `null` for paused/down devices.

### `GET /monitors/{id}` – Get single monitor details (Dashboard)
**Response** `200 OK`
```json
{
  "id": "device001",
  "timeout": 60,
  "status": "active",
  "alert_email": "admin@critmon.com",
  "remaining_seconds": 37
}
```
Identical structure to the list item, but for a single device. Returns `404` if not found.

## Developer’s Choice: Simple operational dashboard

### What was added
Two new read‑only endpoints:
- `GET /monitors` – list all devices with real‑time status
- `GET /monitors/{id}` – detailed view of a single device, including remaining countdown seconds

### Why this matters
The original system would **only alert after a failure** — a purely reactive approach.
With this monitoring, operations teams can:
- **See live countdowns** for every active device.
- **Spot devices that are close to timing out** before an alert fires.
- **Take proactive action** (send a technician, check the network, etc💀) to prevent outages.
- **Check the status of paused or down devices** at a glance without relying on alerts only.

This transforms the Dead Man’s Switch from a blind alarm aletrs into a **true observability tool** that enables **predictive maintenance** and reduces false alarms at the glance.

### How it works
- The store tracks the `timer_start` (monotonic time) whenever a countdown begins.
- The endpoints calculate `remaining_seconds` = `timeout - elapsed` for active monitors.
- Paused or down monitors show `remaining_seconds: null`.

No external dependencies, no extra background jobs, it's just a small, efficient addition that makes the whole system more user‑friendly, lean and robust.

## Tech Stack
- **FastAPI** – async Python web framework
- **uv** – dependency management & environment
- **In‑memory store** with JSON file persistence
- **asyncio** – background countdown timers

<div align= "center">
<hr>
<p>Built with ❤️<p>
</div>