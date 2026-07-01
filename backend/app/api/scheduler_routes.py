from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.scheduler import (
    ScheduleMeetingRequest,
    ScheduleMeetingResponse,
)
from app.services.scheduler_service import SchedulerService

router = APIRouter(
    prefix="/scheduler",
    tags=["Scheduler"],
)


@router.post(
    "/schedule",
    response_model=ScheduleMeetingResponse,
    status_code=201,
)
def schedule_meeting(
    meeting: ScheduleMeetingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SchedulerService.schedule_meeting(
        db,
        meeting,
        current_user,
    )