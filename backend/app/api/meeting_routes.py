from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.meeting import (
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
)
from app.services.meeting_service import MeetingService

router = APIRouter(
    prefix="/meetings",
    tags=["Meetings"],
)


@router.post(
    "/",
    response_model=MeetingResponse,
    status_code=201,
)
def create_meeting(
    meeting: MeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MeetingService.create_meeting(
        db,
        meeting,
        current_user,
    )


@router.get(
    "/",
    response_model=list[MeetingResponse],
)
def get_my_meetings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MeetingService.get_my_meetings(
        db,
        current_user,
    )


@router.put(
    "/{meeting_id}",
    response_model=MeetingResponse,
)
def update_meeting(
    meeting_id: int,
    meeting: MeetingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MeetingService.update_meeting(
        db,
        meeting_id,
        meeting,
        current_user,
    )


@router.delete(
    "/{meeting_id}",
)
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return MeetingService.delete_meeting(
        db,
        meeting_id,
        current_user,
    )