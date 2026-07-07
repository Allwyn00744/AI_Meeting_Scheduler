from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class MeetingCreate(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    location: str | None = None

    @model_validator(mode="after")
    def check_time_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class MeetingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str | None = None
    status: str | None = None

    @model_validator(mode="after")
    def check_time_order(self):
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            raise ValueError("end_time must be after start_time")
        return self


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
