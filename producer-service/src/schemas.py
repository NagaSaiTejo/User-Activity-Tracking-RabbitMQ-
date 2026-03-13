from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional

class UserActivityEvent(BaseModel):
    user_id: int = Field(..., description="ID of the user")
    event_type: str = Field(..., description="Type of event (e.g., 'login', 'logout', 'page_view')")
    timestamp: datetime = Field(..., description="ISO 8601 string of when the event occurred")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context about the event")
