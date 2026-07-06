from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import settings
from app.models.google_credential import GoogleCredential


class GoogleCalendarAPI:

    @staticmethod
    def get_calendar_service(
        credential: GoogleCredential,
    ):
        credentials = Credentials(
            token=credential.access_token,
            refresh_token=credential.refresh_token,
            token_uri=credential.token_uri,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=credential.scopes.split(","),
        )

        return build(
            "calendar",
            "v3",
            credentials=credentials,
        )

    @staticmethod
    def create_calendar_event(
        credential: GoogleCredential,
        title: str,
        description: str,
        start_time,
        end_time,
        location: str | None = None,
    ):
        service = GoogleCalendarAPI.get_calendar_service(
            credential
        )

        event = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_time.isoformat(),
            },
            "end": {
                "dateTime": end_time.isoformat(),
            },
        }

        created_event = (
            service.events()
            .insert(
                calendarId="primary",
                body=event,
            )
            .execute()
        )

        return created_event