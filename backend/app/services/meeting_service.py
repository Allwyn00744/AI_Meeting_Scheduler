from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import date

from app.models.external_meeting_guest import ExternalMeetingGuest
from app.models.meeting import Meeting
from app.models.user import User
from app.repositories.external_meeting_guest_repository import (
    ExternalMeetingGuestRepository,
)
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.resource_repository import ResourceRepository
from app.schemas.meeting import MeetingCreate, MeetingUpdate
from app.services.analytics_service import (
    EVENT_CONFLICT_BLOCKED_OWNER,
    EVENT_CONFLICT_BLOCKED_RESOURCE,
    AnalyticsService,
)
from app.services.conflict_service import ConflictService
from app.services.external_guest_service import ExternalGuestService
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
            AnalyticsService.try_record_event(
                current_user.id,
                EVENT_CONFLICT_BLOCKED_OWNER,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Meeting conflicts with "
                    f"'{existing_meeting.title}'"
                ),
            )

        # Resource booking is optional. When requested, the resource
        # must exist, be active, and be free for this time range -
        # validated before the meeting is created.
        if meeting.resource_id is not None:
            resource = ResourceRepository.get_by_id(
                db,
                meeting.resource_id,
            )

            if resource is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resource not found",
                )

            if not resource.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Resource '{resource.name}' is not active "
                        f"and cannot be booked."
                    ),
                )

            resource_conflict, conflicting_meeting = (
                ConflictService.check_resource_conflict(
                    db,
                    meeting.resource_id,
                    meeting.start_time,
                    meeting.end_time,
                )
            )

            if resource_conflict:
                AnalyticsService.try_record_event(
                    current_user.id,
                    EVENT_CONFLICT_BLOCKED_RESOURCE,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Resource '{resource.name}' is already "
                        f"booked for '{conflicting_meeting.title}'."
                    ),
                )

        # Resolve external guests before writing anything. This path
        # has no participant_ids, so only the owner-collision rule
        # applies (participant_emails is empty).
        resolved_guests = ExternalGuestService.resolve_guests(
            meeting.external_guest_emails,
            current_user.email,
            [],
        )

        # Create the meeting
        db_meeting = Meeting(
            title=meeting.title,
            description=meeting.description,
            start_time=meeting.start_time,
            end_time=meeting.end_time,
            location=meeting.location,
            owner_id=current_user.id,
            resource_id=meeting.resource_id,
        )

        db_meeting = MeetingRepository.create(db, db_meeting)

        if resolved_guests:
            ExternalMeetingGuestRepository.create_many(
                db,
                [
                    ExternalMeetingGuest(
                        meeting_id=db_meeting.id,
                        email=email,
                    )
                    for email in resolved_guests
                ],
            )

        return db_meeting

    @staticmethod
    def get_my_meetings(
        db: Session,
        current_user: User,
        limit: int | None = None,
        offset: int = 0,
    ):
        return MeetingRepository.get_all(
            db,
            current_user.id,
            limit=limit,
            offset=offset,
        )

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

        # Delete Google Calendar event first. Note: this is a
        # best-effort side effect, not part of the same atomic
        # transaction as the database delete below - Google Calendar
        # and PostgreSQL are two separate systems with no distributed
        # transaction between them.
        if meeting.google_event_id:
            GoogleCalendarService.delete_google_calendar_event(
                db=db,
                meeting=meeting,
            )

        # Delete meeting from database. Participant rows are removed
        # automatically at the database level (ON DELETE CASCADE on
        # meeting_participants.meeting_id), so no manual participant
        # cleanup is needed here.
        try:
            MeetingRepository.delete(
                db,
                meeting,
            )
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Unable to delete meeting due to related "
                    "records. Please try again or contact support."
                ),
            )

        return {
            "message": "Meeting deleted successfully"
        }

    @staticmethod
    def search_meetings(
        db: Session,
        keyword: str,
        current_user: User,
        limit: int | None = None,
        offset: int = 0,
    ):
        return MeetingRepository.search_meetings(
            db,
            current_user.id,
            keyword,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def filter_by_status(
        db: Session,
        status: str,
        current_user: User,
        limit: int | None = None,
        offset: int = 0,
    ):
        return MeetingRepository.filter_by_status(
            db,
            current_user.id,
            status,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def filter_by_date(
        db: Session,
        meeting_date: date,
        current_user: User,
        limit: int | None = None,
        offset: int = 0,
    ):
        return MeetingRepository.filter_by_date(
            db,
            current_user.id,
            meeting_date,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def filter_by_date_range(
        db: Session,
        start_date: date,
        end_date: date,
        current_user: User,
        limit: int | None = None,
        offset: int = 0,
    ):
        return MeetingRepository.filter_by_date_range(
            db,
            current_user.id,
            start_date,
            end_date,
            limit=limit,
            offset=offset,
        )
