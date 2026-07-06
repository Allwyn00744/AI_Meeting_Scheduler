from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScheduleMeetingRequest(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    location: str | None = None

    participant_ids: list[int]
    
    repeat: bool = False
    repeat_type: str | None = None
    occurrences: int | None = None


class ScheduleMeetingResponse(BaseModel):
    message: str
    meeting_ids: list[int]

    model_config = ConfigDict(from_attributes=True)

class SuggestedSlot(BaseModel):
    start_time: datetime
    end_time: datetime


class SuggestSlotsResponse(BaseModel):
    slots: list[SuggestedSlot]