from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

# Hard ceiling on how many occurrences a single recurring-series
# request can create. Without this, a caller could pass an
# arbitrarily large `occurrences` value and create thousands of
# meetings (and thousands of Google Calendar events / emails) in one
# request.
MAX_OCCURRENCES = 52

SUPPORTED_REPEAT_TYPES = {"weekly"}


class ScheduleMeetingRequest(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    location: str | None = None
    resource_id: int | None = None

    participant_ids: list[int]

    repeat: bool = False
    repeat_type: str | None = None
    occurrences: int | None = None

    @model_validator(mode="after")
    def validate_request(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")

        if self.repeat:
            if self.repeat_type is None:
                raise ValueError(
                    "repeat_type is required when repeat is true"
                )

            if self.repeat_type not in SUPPORTED_REPEAT_TYPES:
                raise ValueError(
                    f"repeat_type must be one of "
                    f"{sorted(SUPPORTED_REPEAT_TYPES)}"
                )

            if self.occurrences is None or self.occurrences < 1:
                raise ValueError(
                    "occurrences must be at least 1 when repeat is true"
                )

            if self.occurrences > MAX_OCCURRENCES:
                raise ValueError(
                    f"occurrences cannot exceed {MAX_OCCURRENCES}"
                )

        return self


class ScheduleMeetingResponse(BaseModel):
    message: str
    meeting_ids: list[int]

    model_config = ConfigDict(from_attributes=True)


class SuggestedSlot(BaseModel):
    start_time: datetime
    end_time: datetime


class SuggestSlotsResponse(BaseModel):
    slots: list[SuggestedSlot]
