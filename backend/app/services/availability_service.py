from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.availability import Availability
from app.models.user import User
from app.repositories.availability_repository import (
    AvailabilityRepository,
)


from app.schemas.availability import (
    AvailabilityCreate,
    AvailabilityUpdate,
)


class AvailabilityService:

    @staticmethod
    def create_availability(
        db: Session,
        availability: AvailabilityCreate,
        current_user: User,
    ):
        if availability.start_time >= availability.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time",
            )

        db_availability = Availability(
            user_id=current_user.id,
            day_of_week=availability.day_of_week,
            start_time=availability.start_time,
            end_time=availability.end_time,
            is_available=availability.is_available,
        )

        return AvailabilityRepository.create(
            db,
            db_availability,
        )

    @staticmethod
    def get_my_availability(
        db: Session,
        current_user: User,
    ):
        return AvailabilityRepository.get_by_user(
            db,
            current_user.id,
        )

    @staticmethod
    def update_availability(
        db: Session,
        availability_id: int,
        availability_data: AvailabilityUpdate,
        current_user: User,
    ):
        availability = AvailabilityRepository.get_by_id(
            db,
            availability_id,
        )

        if availability is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Availability not found",
            )

        if availability.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        update_data = availability_data.model_dump(
            exclude_unset=True
        )

        # Resolve the effective start/end (existing value unless
        # this update replaces it) so a partial update can't leave
        # start >= end without being caught.
        effective_start = update_data.get(
            "start_time", availability.start_time
        )
        effective_end = update_data.get(
            "end_time", availability.end_time
        )

        if effective_start >= effective_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be before end time",
            )

        for key, value in update_data.items():
            setattr(availability, key, value)

        return AvailabilityRepository.update(
            db,
            availability,
        )

    @staticmethod
    def delete_availability(
        db: Session,
        availability_id: int,
        current_user: User,
    ):
        availability = AvailabilityRepository.get_by_id(
            db,
            availability_id,
        )

        if availability is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Availability not found",
            )

        if availability.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        AvailabilityRepository.delete(
            db,
            availability,
        )

        return {
            "message": "Availability deleted successfully"
        }

    @staticmethod
    def is_user_available(
        db: Session,
        user_id: int,
        meeting_start: datetime,
        meeting_end: datetime,
    ):
        # The Availability model only stores a single time-of-day
        # window per day of week (e.g. "Monday 09:00-17:00"). A
        # meeting that spans across midnight, or across more than one
        # calendar day, cannot be correctly evaluated against a
        # single day's window - comparing only the .time() components
        # would silently compare the wrong things (e.g. a 23:00-01:00
        # meeting would compare 23:00/01:00 against a daytime window
        # and could pass or fail for the wrong reason). Treat any such
        # meeting as unavailable rather than risk a wrong answer.
        if meeting_start.date() != meeting_end.date():
            return False

        day = meeting_start.strftime("%A")

        availability = (
            AvailabilityRepository.get_by_user_and_day(
                db,
                user_id,
                day,
            )
        )

        if availability is None:
            return False

        return (
            availability.start_time <= meeting_start.time()
            and availability.end_time >= meeting_end.time()
        )
