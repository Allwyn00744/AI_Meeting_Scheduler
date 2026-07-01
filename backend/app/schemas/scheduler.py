from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScheduleMeetingRequest(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    location: str | None = None

    participant_ids: list[int]


class ScheduleMeetingResponse(BaseModel):
    message: str
    meeting_id: int

    model_config = ConfigDict(from_attributes=True)