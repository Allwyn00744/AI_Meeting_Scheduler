from fastapi import FastAPI

from app.api.user_routes import router as user_router

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