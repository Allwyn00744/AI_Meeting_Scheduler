import logging
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.user import User

from app.repositories.meeting_repository import MeetingRepository
from app.repositories.user_repository import UserRepository
from app.repositories.meeting_participant_repository import (
    MeetingParticipantRepository,
)

from app.schemas.meeting import MeetingUpdate
from app.schemas.scheduler import (
    ScheduleMeetingRequest,
    SuggestSlotsResponse,
    SuggestedSlot,
)

from app.services.email_service import EmailService
from app.services.conflict_service import ConflictService
from app.services.availability_service import AvailabilityService
from app.services.google_calendar_service import GoogleCalendarService


logger = logging.getLogger(__name__)


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
        Schedule a meeting after validating all occurrences.
        """

        # ---------------------------------------
        # Step 1: Validate request participants
        # ---------------------------------------

        if len(meeting.participant_ids) != len(
            set(meeting.participant_ids)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate participants are not allowed.",
            )

        if current_user.id in meeting.participant_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting owner cannot be a participant.",
            )

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

        # ---------------------------------------
        # Step 2: Determine number of occurrences
        # ---------------------------------------

        repeat_count = 1

        if (
            meeting.repeat
            and meeting.repeat_type == "weekly"
            and meeting.occurrences
        ):
            repeat_count = meeting.occurrences

        # ---------------------------------------
        # Step 3: Build ALL occurrences
        # ---------------------------------------

        occurrences = []

        for i in range(repeat_count):
            meeting_start = (
                meeting.start_time
                + timedelta(days=7 * i)
            )

            meeting_end = (
                meeting.end_time
                + timedelta(days=7 * i)
            )

            occurrences.append(
                (meeting_start, meeting_end)
            )

        # ---------------------------------------
        # Step 4: Validate ALL occurrences
        # ---------------------------------------

        for index, (meeting_start, meeting_end) in enumerate(
            occurrences,
            start=1,
        ):

            # Owner conflict
            owner_conflict, owner_meeting = (
                ConflictService.check_user_conflict(
                    db,
                    current_user.id,
                    meeting_start,
                    meeting_end,
                )
            )

            if owner_conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Occurrence {index} conflicts with "
                        f"'{owner_meeting.title}'."
                    ),
                )

            # Owner availability
            if not AvailabilityService.is_user_available(
                db,
                current_user.id,
                meeting_start,
                meeting_end,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Occurrence {index} is outside "
                        "your available working hours."
                    ),
                )

            # Participant conflicts
            conflict, user_id, conflict_meeting = (
                ConflictService.check_all_participants(
                    db,
                    meeting.participant_ids,
                    meeting_start,
                    meeting_end,
                )
            )

            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Occurrence {index}: participant "
                        f"{user_id} has a scheduling conflict "
                        f"({conflict_meeting.title})."
                    ),
                )

            # Participant availability
            for user_id in meeting.participant_ids:

                if not AvailabilityService.is_user_available(
                    db,
                    user_id,
                    meeting_start,
                    meeting_end,
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Occurrence {index}: participant "
                            f"{user_id} is not available."
                        ),
                    )

        # ---------------------------------------
        # Step 5: Create only after ALL pass
        # ---------------------------------------

        created_meetings = []

        for meeting_start, meeting_end in occurrences:

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

            if participants:
                MeetingParticipantRepository.create_many(
                    db,
                    participants,
                )

            try:
                event = (
                    GoogleCalendarService
                    .create_google_calendar_event(
                        db=db,
                        user_id=current_user.id,
                        title=db_meeting.title,
                        description=db_meeting.description or "",
                        start_time=db_meeting.start_time,
                        end_time=db_meeting.end_time,
                        location=db_meeting.location,
                    )
                )

                db_meeting.google_event_id = event.get("id")
                db_meeting.google_event_link = event.get(
                    "htmlLink"
                )
                db_meeting.google_meet_link = event.get(
                    "hangoutLink"
                )

                db.commit()
                db.refresh(db_meeting)

                logger.info(
                    "Google Calendar event created successfully. "
                    "meeting_id=%s google_event_id=%s "
                    "meet_link_created=%s",
                    db_meeting.id,
                    event.get("id"),
                    event.get("hangoutLink") is not None,
                )

            except Exception:
                logger.exception(
                    "Google Calendar integration failed. "
                    "meeting_id=%s",
                    db_meeting.id,
                )

            created_meetings.append(db_meeting.id)

        # ---------------------------------------
        # Step 6: Send participant invitations
        # ---------------------------------------

        if meeting.participant_ids:

            participant_users = (
                UserRepository.get_users_by_ids(
                    db,
                    meeting.participant_ids,
                )
            )

            for participant in participant_users:

                EmailService.send_meeting_invitation(
                    to_email=participant.email,
                    meeting_title=meeting.title,
                    start_time=meeting.start_time,
                    end_time=meeting.end_time,
                    location=meeting.location,
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

            return SuggestSlotsResponse(
                slots=[
                    SuggestedSlot(
                        start_time=suggested_start,
                        end_time=suggested_end,
                    )
                ]
            )

    @staticmethod
    def update_meeting(
        db: Session,
        meeting_id: int,
        meeting_data: MeetingUpdate,
        current_user: User,
    ):
        db_meeting = MeetingRepository.get_by_id(
            db,
            meeting_id,
        )

        if db_meeting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found.",
            )

        if db_meeting.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own meetings.",
            )

        update_data = meeting_data.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(db_meeting, key, value)

        MeetingRepository.update(
            db,
            db_meeting,
        )

        if db_meeting.google_event_id:
            GoogleCalendarService.update_google_calendar_event(
                db,
                db_meeting,
            )

        return db_meeting