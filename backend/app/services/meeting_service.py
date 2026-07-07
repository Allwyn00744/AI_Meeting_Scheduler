from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from app.models.meeting import Meeting
from app.models.user import User
from app.repositories.meeting_repository import MeetingRepository
from app.schemas.meeting import MeetingCreate, MeetingUpdate
from app.services.conflict_service import ConflictService
from app.services.google_calendar_service import GoogleCalendarService
from app.services.google_calendar_service import GoogleCalendarService

class MeetingService:

    @staticmethod
    def create_meeting(
        db: Session,
        meeting: MeetingCreate,
        current_user: User,
    ):
        # Get all meetings of the current user
        existing_meetings = MeetingRepository.get_user_meetings(
            db,
            current_user.id,
        )

        # Check for conflicts
        conflict, existing_meeting = ConflictService.has_time_conflict(
            meeting.start_time,
            meeting.end_time,
            existing_meetings,
        )

        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Meeting conflicts with "
                    f"'{existing_meeting.title}'"
                ),
            )

        # Create the meeting
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

        meeting = MeetingRepository.update(db, meeting)

        # Sync with Google Calendar
        if meeting.google_event_id:
            GoogleCalendarService.update_google_calendar_event(
                db=db,
                meeting=meeting,
            )

        return meeting

    @staticmethod
    def delete_meeting(
        db: Session,
        meeting_id: int,
        current_user: User,
    ):
        meeting = MeetingRepository.get_by_id(
            db,
            meeting_id,
        )

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

        # Delete Google Calendar event first
        if meeting.google_event_id:
            GoogleCalendarService.delete_google_calendar_event(
                db=db,
                meeting=meeting,
            )

        # Delete meeting from database
        MeetingRepository.delete(
            db,
            meeting,
        )

        return {
            "message": "Meeting deleted successfully"
        }
    @staticmethod
    def search_meetings(
        db: Session,
        keyword: str,
        current_user: User,
    ):
        return MeetingRepository.search_meetings(
            db,
            current_user.id,
            keyword,
        )

    @staticmethod
    def filter_by_status(
        db: Session,
        status: str,
        current_user: User,
    ):
        return MeetingRepository.filter_by_status(
            db,
            current_user.id,
            status,
        )
    @staticmethod
    def filter_by_date(
        db: Session,
        meeting_date: date,
        current_user: User,
    ):
        return MeetingRepository.filter_by_date(
            db,
            current_user.id,
            meeting_date,
        )
    @staticmethod
    def filter_by_date_range(
        db: Session,
        start_date: date,
        end_date: date,
        current_user: User,
    ):
        return MeetingRepository.filter_by_date_range(
            db,
            current_user.id,
            start_date,
            end_date,
        )