
from fastapi import APIRouter, Request,Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.calendar.google_oauth import GoogleOAuthService
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.db.database import get_db
from app.services.google_calendar_service import GoogleCalendarService


router = APIRouter(
    prefix="/google",
    tags=["Google Calendar"],
)


@router.get("/login")
def google_login():
    authorization_url = GoogleOAuthService.get_authorization_url(
        state="6"   # Replace with your actual logged-in user's ID
    )

    return RedirectResponse(url=authorization_url)


@router.get("/callback")
def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    flow = GoogleOAuthService.create_flow()

    flow.fetch_token(
        authorization_response=str(request.url)
    )

    credentials = flow.credentials

    # Read the user_id from OAuth state
    user_id = int(request.query_params["state"])

    GoogleCalendarService.save_google_credentials(
        db=db,
        user_id=user_id,
        credentials=credentials,
    )

    return {
        "message": "Google account connected successfully",
        "google_credentials_saved": True,
    }