import logging
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
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

# How many consecutive one-hour slots suggest_slots will try before
# giving up and telling the caller no slot was found, instead of
# silently returning None (which previously broke the declared
# response_model whenever the search was exhausted).
MAX_SLOT_ATTEMPTS = 8

# suggest_reschedule_slots: fixed candidate step, default search
# window, and cap on how many suggestions are returned.
RESCHEDULE_SEARCH_INTERVAL_MINUTES = 15
DEFAULT_RESCHEDULE_WINDOW_DAYS = 7
MAX_RESCHEDULE_SUGGESTIONS = 5


class SchedulerService:
    """
    Handles intelligent meeting scheduling.
    """

    @staticmethod
    def _validate_participants(db: Session, current_user: User, meeting):
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

    @staticmethod
    def _cleanup_created_occurrences(
        db: Session,
        created_meeting_ids: list[int],
    ):
        """
        Best-effort compensation for a recurring-series request that
        fails partway through creating its occurrences. Deletes any
        meetings already created in this batch (participant rows are
        removed automatically via ON DELETE CASCADE) and attempts to
        remove their Google Calendar events too, so a failed request
        doesn't leave a silent partial series behind.

        This is a compensating cleanup, not a database transaction:
        PostgreSQL and Google Calendar are two separate systems and
        this method does not make the overall operation atomic across
        both.
        """
        for meeting_id in created_meeting_ids:
            meeting = MeetingRepository.get_by_id(db, meeting_id)

            if meeting is None:
                continue

            if meeting.google_event_id:
                try:
                    GoogleCalendarService.delete_google_calendar_event(
                        db=db,
                        meeting=meeting,
                    )
                except HTTPException:
                    logger.warning(
                        "Cleanup: failed to delete Google Calendar "
                        "event for meeting_id=%s during rollback of "
                        "a failed recurring series.",
                        meeting_id,
                    )

            try:
                MeetingRepository.delete(db, meeting)
            except IntegrityError:
                db.rollback()
                logger.error(
                    "Cleanup: failed to delete meeting_id=%s during "
                    "rollback of a failed recurring series.",
                    meeting_id,
                )

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

        SchedulerService._validate_participants(db, current_user, meeting)

        # ---------------------------------------
        # Step 2: Determine number of occurrences
        # ---------------------------------------
        # (schemas.scheduler.ScheduleMeetingRequest already validates
        # repeat_type and caps occurrences at MAX_OCCURRENCES, so this
        # only needs to read the already-validated value.)

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

        try:
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

                created_meetings.append(db_meeting.id)

                # Google Calendar sync is a best-effort side effect,
                # deliberately isolated from the database transaction
                # above: PostgreSQL and Google Calendar are two
                # separate systems with no distributed transaction
                # between them. A Calendar failure here does not
                # cause the meeting occurrence itself to be rolled
                # back or the series to be aborted.
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
                        "meeting_id=%s meet_link_created=%s",
                        db_meeting.id,
                        event.get("hangoutLink") is not None,
                    )

                except Exception:
                    logger.exception(
                        "Google Calendar integration failed. "
                        "meeting_id=%s",
                        db_meeting.id,
                    )

        except IntegrityError:
            db.rollback()
            logger.error(
                "Recurring meeting series creation failed partway "
                "through. Rolling back %s already-created "
                "occurrence(s).",
                len(created_meetings),
            )
            SchedulerService._cleanup_created_occurrences(
                db,
                created_meetings,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Failed to create the recurring meeting series "
                    "due to a database conflict. No occurrences were "
                    "kept - please try again."
                ),
            )

        # ---------------------------------------
        # Step 6: Send participant invitations
        # ---------------------------------------
        # Best-effort: an email/SMTP failure here must not turn an
        # already-successful scheduling request into a 500 response,
        # since the meeting(s) are already committed at this point.

        if meeting.participant_ids:

            participant_users = (
                UserRepository.get_users_by_ids(
                    db,
                    meeting.participant_ids,
                )
            )

            for participant in participant_users:

                EmailService.try_send_meeting_invitation(
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
        Suggest the first available meeting slot, checking both
        conflicts and declared working-hours availability for the
        owner and every participant. Raises a 404 (rather than
        silently returning None) if no slot is found within the
        search window.
        """

        SchedulerService._validate_participants(db, current_user, meeting)

        suggested_start = meeting.start_time
        suggested_end = meeting.end_time

        for _ in range(MAX_SLOT_ATTEMPTS):

            owner_meetings = (
                MeetingRepository.get_meetings_between(
                    db,
                    current_user.id,
                    suggested_start,
                    suggested_end,
                )
            )

            owner_available = AvailabilityService.is_user_available(
                db,
                current_user.id,
                suggested_start,
                suggested_end,
            )

            if owner_meetings or not owner_available:
                suggested_start += timedelta(hours=1)
                suggested_end += timedelta(hours=1)
                continue

            participant_blocked = False

            for participant_id in meeting.participant_ids:

                participant_meetings = (
                    MeetingRepository.get_meetings_between(
                        db,
                        participant_id,
                        suggested_start,
                        suggested_end,
                    )
                )

                participant_available = (
                    AvailabilityService.is_user_available(
                        db,
                        participant_id,
                        suggested_start,
                        suggested_end,
                    )
                )

                if participant_meetings or not participant_available:
                    participant_blocked = True
                    break

            if participant_blocked:
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

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No available slot found for the owner and all "
                "participants within the searched window."
            ),
        )

    @staticmethod
    def suggest_reschedule_slots(
        db: Session,
        meeting_id: int,
        current_user: User,
        window_days: int = DEFAULT_RESCHEDULE_WINDOW_DAYS,
    ):
        """
        Suggest up to MAX_RESCHEDULE_SUGGESTIONS alternative slots for
        an existing meeting, searching in fixed
        RESCHEDULE_SEARCH_INTERVAL_MINUTES increments across
        `window_days` days starting from the meeting's own
        start_time. The meeting's own duration is preserved for every
        candidate.

        Read-only: this never modifies the meeting, its participants,
        or any external system (Google Calendar/Meet, email) - it
        only returns candidate slots for the caller to act on.
        Raises 404 if no valid slot is found anywhere in the window.
        """
        meeting = MeetingRepository.get_by_id(db, meeting_id)

        if meeting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found.",
            )

        is_owner = meeting.owner_id == current_user.id
        is_participant = (
            MeetingParticipantRepository.get_by_meeting_and_user(
                db,
                meeting_id,
                current_user.id,
            )
            is not None
        )

        if not is_owner and not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You must be the meeting owner or a participant "
                    "to request reschedule suggestions."
                ),
            )

        duration = meeting.end_time - meeting.start_time

        participant_ids = [
            participant.user_id
            for participant in (
                MeetingParticipantRepository.get_by_meeting(
                    db,
                    meeting_id,
                )
            )
        ]

        search_end = meeting.start_time + timedelta(days=window_days)
        candidate_start = meeting.start_time
        step = timedelta(minutes=RESCHEDULE_SEARCH_INTERVAL_MINUTES)

        suggestions = []

        while (
            candidate_start + duration <= search_end
            and len(suggestions) < MAX_RESCHEDULE_SUGGESTIONS
        ):
            candidate_end = candidate_start + duration

            owner_meetings = [
                other
                for other in MeetingRepository.get_meetings_between(
                    db,
                    meeting.owner_id,
                    candidate_start,
                    candidate_end,
                )
                if other.id != meeting_id
            ]

            owner_available = AvailabilityService.is_user_available(
                db,
                meeting.owner_id,
                candidate_start,
                candidate_end,
            )

            if owner_meetings or not owner_available:
                candidate_start += step
                continue

            participant_blocked = False

            for participant_id in participant_ids:

                participant_meetings = [
                    other
                    for other in MeetingRepository.get_meetings_between(
                        db,
                        participant_id,
                        candidate_start,
                        candidate_end,
                    )
                    if other.id != meeting_id
                ]

                participant_available = (
                    AvailabilityService.is_user_available(
                        db,
                        participant_id,
                        candidate_start,
                        candidate_end,
                    )
                )

                if participant_meetings or not participant_available:
                    participant_blocked = True
                    break

            if participant_blocked:
                candidate_start += step
                continue

            suggestions.append(
                SuggestedSlot(
                    start_time=candidate_start,
                    end_time=candidate_end,
                )
            )

            candidate_start += step

        if not suggestions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No available reschedule slot found for the "
                    "owner and all participants within the searched "
                    "window."
                ),
            )

        return SuggestSlotsResponse(slots=suggestions)

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
