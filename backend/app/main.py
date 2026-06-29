from fastapi import FastAPI

from app.api.user_routes import router as user_router
from app.api.auth_routes import router as auth_router
from app.api.meeting_routes import router as meeting_router
from app.api.meeting_participant_routes import router as participant_router


app = FastAPI(
    title="AI Meeting Scheduler API",
    version="1.0.0"
)

# Root Endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to AI Meeting Scheduler API"
    }

# Register User Routes
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(meeting_router)
app.include_router(participant_router)