from pydantic import BaseModel
from typing import Optional

class MonitorCreate(BaseModel):
    id: str
    timeout: int                # secs
    alert_email: Optional[str] = None

class MonitorOut(BaseModel):
    id: str
    timeout: int
    status: str                 # active, paused, down
    alert_email: Optional[str]