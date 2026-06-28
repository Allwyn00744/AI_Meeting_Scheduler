from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.user import User
from app.repositories.meeting_repository import MeetingRepository
from app.schemas.meeting import MeetingCreate, MeetingUpdate


class MeetingService:

    @staticmethod
    def create_meeting(
        db: Session,
        meeting: MeetingCreate,
        current_user: User,
    ):
        db_meeting = Meeting(
            title=meeting.title,
            description=meeting.description,
            start_time=meeting.start_time,
            end_time=meeting.end_time,
            location=meeting.location,
            owner_id=current_user.id,
        )

        return MeetingRepository.create(db, db_meeting)

    @staticmethod
    def get_my_meetings(
        db: Session,
        current_user: User,
    ):
        return MeetingRepository.get_all(db, current_user.id)

    @staticmethod
    def update_meeting(
        db: Session,
        meeting_id: int,
        meeting_data: MeetingUpdate,
        current_user: User,
    ):
        meeting = MeetingRepository.get_by_id(db, meeting_id)

        if meeting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found",
            )

        if meeting.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        update_data = meeting_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(meeting, key, value)

        return MeetingRepository.update(db, meeting)

    @staticmethod
    def delete_meeting(
        db: Session,
        meeting_id: int,
        current_user: User,
    ):
        meeting = MeetingRepository.get_by_id(db, meeting_id)

        if meeting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found",
            )

        if meeting.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        MeetingRepository.delete(db, meeting)

        return {
            "message": "Meeting deleted successfully"
        }