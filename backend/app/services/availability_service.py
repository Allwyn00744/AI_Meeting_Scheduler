from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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

        if (
            "start_time" in update_data
            and "end_time" in update_data
            and update_data["start_time"] >= update_data["end_time"]
        ):
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