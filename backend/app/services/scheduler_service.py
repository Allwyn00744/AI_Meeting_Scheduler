from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.meeting import Meeting
from app.models.meeting_participant import MeetingParticipant
from app.models.user import User

from app.repositories.meeting_repository import MeetingRepository
from app.repositories.meeting_participant_repository import (
    MeetingParticipantRepository,
)

from app.schemas.scheduler import ScheduleMeetingRequest

from app.services.conflict_service import ConflictService

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

        # Step 3: Create Meeting
        db_meeting = Meeting(
            title=meeting.title,
            description=meeting.description,
            start_time=meeting.start_time,
            end_time=meeting.end_time,
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

        return {
            "message": "Meeting scheduled successfully",
            "meeting_id": db_meeting.id,
        }
    
    