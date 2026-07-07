import logging

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.calendar.google_oauth import GoogleOAuthService
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.db.database import get_db
from app.services.google_calendar_service import GoogleCalendarService
from app.services.google_oauth_state_service import GoogleOAuthStateService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/google",
    tags=["Google Calendar"],
)


@router.get("/login")
def google_login(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state = GoogleOAuthStateService.create_state(
        db,
        current_user.id,
    )

    authorization_url = GoogleOAuthService.get_authorization_url(
        state=state,
    )

    return RedirectResponse(url=authorization_url)


@router.get("/callback")
def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    error = request.query_params.get("error")

    if error:
        logger.warning(
            "Google OAuth consent was denied or errored. error=%s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google authorization was not completed.",
        )

    state_value = request.query_params.get("state")

    if not state_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OAuth state.",
        )

    user_id = GoogleOAuthStateService.verify_and_consume_state(
        db,
        state_value,
    )

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already-used OAuth state.",
        )

    flow = GoogleOAuthService.create_flow()

    try:
        flow.fetch_token(
            authorization_response=str(request.url)
        )
    except Exception:
        logger.exception(
            "Google OAuth token exchange failed. user_id=%s",
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to complete Google authorization.",
        )

    credentials = flow.credentials

    GoogleCalendarService.save_google_credentials(
        db=db,
        user_id=user_id,
        credentials=credentials,
    )

    logger.info(
        "Google account connected successfully. user_id=%s",
        user_id,
    )

    return {
        "message": "Google account connected successfully",
        "google_credentials_saved": True,
    }