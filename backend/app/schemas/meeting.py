from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MeetingCreate(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    location: str | None = None


class MeetingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str | None = None
    status: str | None = None


class MeetingResponse(BaseModel):
    id: int
    title: str
    description: str | None
    start_time: datetime
    end_time: datetime
    location: str | None
    status: str
    owner_id: int

    model_config = ConfigDict(from_attributes=True)