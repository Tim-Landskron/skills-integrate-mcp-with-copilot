"""
High School Management System API

A simple FastAPI application that allows students to view extracurricular
activities and teachers to manage signups.
"""

import logging
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from src.auth import TEACHERS_FILE, hash_password, load_teachers, verify_password

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

session_secret = os.environ.get("SESSION_SECRET")
if not session_secret and os.environ.get("APP_ENV") == "production":
    raise RuntimeError("SESSION_SECRET must be set in production")
if not session_secret:
    session_secret = secrets.token_urlsafe(32)
    logging.warning(
        "SESSION_SECRET is unset; teacher sessions will end when the server restarts"
    )

DUMMY_CREDENTIAL = hash_password(secrets.token_urlsafe(32))

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    session_cookie="teacher_session",
    max_age=60 * 60 * 8,
    same_site="strict",
    https_only=(
        os.environ.get("APP_ENV") == "production"
        or os.environ.get("COOKIE_SECURE", "").lower() == "true"
    ),
)

current_dir = Path(__file__).parent
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(current_dir, "static")),
    name="static",
)

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)


def require_teacher(request: Request) -> None:
    if request.session.get("role") != "teacher":
        raise HTTPException(status_code=401, detail="Teacher login required")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/auth/session")
def get_session(request: Request):
    username = request.session.get("username")
    return {
        "authenticated": request.session.get("role") == "teacher",
        "username": username,
    }


@app.post("/auth/login")
def login(credentials: LoginRequest, request: Request):
    try:
        teachers = load_teachers()
    except RuntimeError as error:
        status_code = 503 if not TEACHERS_FILE.exists() else 500
        raise HTTPException(status_code=status_code, detail=str(error)) from error

    credential = teachers.get(credentials.username)
    password_is_valid = verify_password(
        credentials.password, credential or DUMMY_CREDENTIAL
    )
    if credential is None or not password_is_valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    request.session.clear()
    request.session["role"] = "teacher"
    request.session["username"] = credentials.username
    return {"authenticated": True, "username": credentials.username}


@app.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"authenticated": False}


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, request: Request):
    """Sign up a student for an activity."""
    require_teacher(request)

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, request: Request):
    """Unregister a student from an activity."""
    require_teacher(request)

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity",
        )

    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
