from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import traceback

from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.user import User

from app.repositories.meeting_repository import MeetingRepository
from app.repositories.user_repository import UserRepository
from app.repositories.meeting_participant_repository import (
    MeetingParticipantRepository,
)
from app.services.email_service import EmailService
from app.repositories.user_repository import UserRepository

from app.schemas.scheduler import (
    ScheduleMeetingRequest,
    SuggestSlotsResponse,
    SuggestedSlot,
)

from app.services.conflict_service import ConflictService
from app.services.availability_service import AvailabilityService
from app.services.google_calendar_service import GoogleCalendarService

class SchedulerService:
    """
    Handles intelligent meeting scheduling.
    """

    @staticmethod
    def schedule_meeting(
        db: Session,
        meeting: ScheduleMeetingRequest,
        current_user: User,
    ):
        """
        Schedule a meeting after validating conflicts.
        """
        # Validate duplicate participants
        if len(meeting.participant_ids) != len(set(meeting.participant_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate participants are not allowed.",
            )

        # Prevent owner from being added as a participant
        if current_user.id in meeting.participant_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting owner cannot be a participant.",
            )
        # Validate participant IDs
        for user_id in meeting.participant_ids:
            user = UserRepository.get_user_by_id(
                db,
                user_id,
            )

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} does not exist.",
                )
        # Step 1: Check owner's calendar
        owner_conflict, owner_meeting = (
            ConflictService.check_user_conflict(
                db,
                current_user.id,
                meeting.start_time,
                meeting.end_time,
            )
        )

        if owner_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"You already have a meeting: "
                    f"{owner_meeting.title}"
                ),
            )
        # Step 1.5: Check owner's availability
        if not AvailabilityService.is_user_available(
            db,
            current_user.id,
            meeting.start_time,
            meeting.end_time,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting is outside your available working hours.",
            )

        # Step 2: Check participant conflicts
        conflict, user_id, conflict_meeting = (
            ConflictService.check_all_participants(
                db,
                meeting.participant_ids,
                meeting.start_time,
                meeting.end_time,
            )
        )

        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Participant {user_id} has a scheduling conflict "
                    f"({conflict_meeting.title})"
                ),
            )
        # Step 2.5: Check participants' availability
        for user_id in meeting.participant_ids:

            if not AvailabilityService.is_user_available(
                db,
                user_id,
                meeting.start_time,
                meeting.end_time,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Participant {user_id} is not available "
                        "during the requested time."
                    ),
                )
        # Step 3: Create Meeting
        created_meetings = []

        repeat_count = 1

        if (
            meeting.repeat
            and meeting.repeat_type == "weekly"
            and meeting.occurrences
        ):
            repeat_count = meeting.occurrences

        for i in range(repeat_count):

            meeting_start = meeting.start_time + timedelta(days=7 * i)
            meeting_end = meeting.end_time + timedelta(days=7 * i)

            db_meeting = Meeting(
                title=meeting.title,
                description=meeting.description,
                start_time=meeting_start,
                end_time=meeting_end,
                location=meeting.location,
                owner_id=current_user.id,
            )

            db_meeting = MeetingRepository.create(
                db,
                db_meeting,
            )

            participants = []

            for user_id in meeting.participant_ids:
                participants.append(
                    MeetingParticipant(
                        meeting_id=db_meeting.id,
                        user_id=user_id,
                        status="Pending",
                    )
                )

            MeetingParticipantRepository.create_many(
                db,
                participants,
            )
            try:
                event = GoogleCalendarService.create_google_calendar_event(
                    db=db,
                    user_id=current_user.id,
                    title=db_meeting.title,
                    description=db_meeting.description or "",
                    start_time=db_meeting.start_time,
                    end_time=db_meeting.end_time,
                    location=db_meeting.location,
                )

                print("=" * 50)
                print("Google Calendar Event Created Successfully")
                print(f"Event ID   : {event.get('id')}")
                print(f"Event Link : {event.get('htmlLink')}")
                print("=" * 50)

            except Exception:
                print("=" * 50)
                print("Google Calendar Integration Failed")
                traceback.print_exc()
                print("=" * 50)

            created_meetings.append(db_meeting.id)

            # Send meeting invitations
        if meeting.participant_ids:

            participant_users = UserRepository.get_users_by_ids(
                db,
                meeting.participant_ids,
            )

            for participant in participant_users:
                EmailService.send_meeting_invitation(
                    to_email=participant.email,
                    meeting_title=db_meeting.title,
                    start_time=db_meeting.start_time,
                    end_time=db_meeting.end_time,
                    location=db_meeting.location,
                )

                return {
                    "message": "Meeting(s) scheduled successfully",
                    "meeting_ids": created_meetings,
                }
    
    @staticmethod
    def suggest_slots(
        db: Session,
        meeting: ScheduleMeetingRequest,
        current_user: User,
    ):
        """
        Suggest the first available meeting slot.
        """

        suggested_start = meeting.start_time
        suggested_end = meeting.end_time

        # Try up to the next 8 one-hour slots
        for _ in range(8):

            # Check owner's meetings
            owner_meetings = (
                MeetingRepository.get_meetings_between(
                    db,
                    current_user.id,
                    suggested_start,
                    suggested_end,
                )
            )

            if owner_meetings:
                suggested_start += timedelta(hours=1)
                suggested_end += timedelta(hours=1)
                continue

            # Check participants' meetings
            participant_busy = False

            for participant_id in meeting.participant_ids:

                participant_meetings = (
                    MeetingRepository.get_meetings_between(
                        db,
                        participant_id,
                        suggested_start,
                        suggested_end,
                    )
                )

                if participant_meetings:
                    participant_busy = True
                    break

            if participant_busy:
                suggested_start += timedelta(hours=1)
                suggested_end += timedelta(hours=1)
                continue

            # Everyone is free
            return SuggestSlotsResponse(
                slots=[
                    SuggestedSlot(
                        start_time=suggested_start,
                        end_time=suggested_end,
                    )
                ]
            )