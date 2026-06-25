from fastapi import FastAPI

app = FastAPI(
    title="AI Meeting Scheduler API",
    version="1.0.0",
    description="AI Meeting Scheduler Backend"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to AI Meeting Scheduler API"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }