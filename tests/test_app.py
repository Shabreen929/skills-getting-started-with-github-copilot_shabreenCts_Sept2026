import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    isolated_activities = copy.deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", isolated_activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    # Arrange
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 9
    assert "Chess Club" in activities
    assert set(activities["Chess Club"]) == expected_fields


def test_signup_adds_student_and_returns_success_message(client):
    # Arrange
    email = "new.student@mergington.edu"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert email in participants


def test_signup_rejects_duplicate_student(client):
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    # Arrange

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_full_activity(client):
    # Arrange
    app_module.activities["Chess Club"]["participants"] = [
        f"student{number}@mergington.edu" for number in range(12)
    ]

    # Act
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_signup_requires_email(client):
    # Arrange

    # Act
    response = client.post("/activities/Chess%20Club/signup")

    # Assert
    assert response.status_code == 422


def test_remove_deletes_registered_student(client):
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = client.post("/activities/Chess%20Club/remove", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert email not in participants


def test_remove_rejects_unregistered_student(client):
    # Arrange
    email = "not.registered@mergington.edu"

    # Act
    response = client.post("/activities/Chess%20Club/remove", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not registered for this activity"


def test_remove_rejects_unknown_activity(client):
    # Arrange

    # Act
    response = client.post(
        "/activities/Unknown%20Club/remove",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_requires_email(client):
    # Arrange

    # Act
    response = client.post("/activities/Chess%20Club/remove")

    # Assert
    assert response.status_code == 422


def test_signup_then_remove_updates_activity_state(client):
    # Arrange
    email = "new.student@mergington.edu"

    # Act
    signup_response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )
    remove_response = client.post(
        "/activities/Chess%20Club/remove",
        params={"email": email},
    )

    # Assert
    assert signup_response.status_code == 200
    assert remove_response.status_code == 200
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert email not in participants