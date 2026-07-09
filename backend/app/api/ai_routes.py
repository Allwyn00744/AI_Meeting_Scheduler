"""
AI endpoints — text scheduling, meeting summary, and follow-up generation.

All AI output is validated by Pydantic schemas before any application
service method is called. No endpoint writes to the database directly.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.ai import (
    FollowUpDraftResponse,
    MeetingNotesRequest,
    MeetingSummaryResponse,
    TextScheduleRequest,
)
from app.schemas.scheduler import ScheduleMeetingResponse
from app.services.ai_meeting_service import AIMeetingService

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post(
    "/schedule-text",
    response_model=ScheduleMeetingResponse,
    status_code=201,
    summary="Schedule a meeting from natural language",
)
def schedule_from_text(
    body: TextScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convert a natural-language scheduling request into a confirmed
    meeting. The AI extracts the intent; all standard availability and
    conflict checks run through the existing SchedulerService.
    """
    return AIMeetingService.schedule_from_text(
        db=db,
        text=body.text,
        current_user=current_user,
    )


@router.post(
    "/meetings/{meeting_id}/summary",
    response_model=MeetingSummaryResponse,
    summary="Summarise meeting notes and extract action items",
)
def summarize_meeting(
    meeting_id: int,
    body: MeetingNotesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a concise structured summary and extract action items from
    the supplied meeting notes or transcript. The authenticated user
    must be the meeting owner or a registered participant.

    On success, the notes, summary, and action items are persisted
    (overwriting any prior generation for this meeting) via
    MeetingIntelligenceService. See GET /meetings/{meeting_id}/notes,
    /summary, and /action-items to read persisted records afterward.
    """
    return AIMeetingService.summarize_meeting(
        db=db,
        meeting_id=meeting_id,
        notes=body.notes,
        current_user=current_user,
    )


@router.post(
    "/meetings/{meeting_id}/follow-up",
    response_model=FollowUpDraftResponse,
    summary="Generate a follow-up email draft",
)
def generate_follow_up(
    meeting_id: int,
    body: MeetingNotesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a professional follow-up email draft based on the meeting
    details and supplied notes. The email is NOT sent automatically —
    only the draft is returned. The authenticated user must be the
    meeting owner or a registered participant.
    """
    return AIMeetingService.generate_follow_up(
        db=db,
        meeting_id=meeting_id,
        notes=body.notes,
        current_user=current_user,
    )
