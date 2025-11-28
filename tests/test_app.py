from fastapi.testclient import TestClient
import pytest

from src import app as app_module


client = TestClient(app_module.app)


def create_temp_activity(name, max_participants=2, participants=None):
    if participants is None:
        participants = []
    app_module.activities[name] = {
        "description": "Temporary activity for tests",
        "schedule": "Now",
        "max_participants": max_participants,
        "participants": participants.copy(),
    }


def remove_temp_activity(name):
    app_module.activities.pop(name, None)


def test_get_activities_structure():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_adds_participant_and_prevents_duplicate():
    name = "Test Signup Activity"
    create_temp_activity(name, max_participants=5, participants=["a@x.com"])
    try:
        # signup a new user
        r1 = client.post(f"/activities/{name}/signup?email=newuser@example.com")
        assert r1.status_code == 200
        assert "Signed up newuser@example.com" in r1.json().get("message", "")

        # verify participant added
        all_activities = client.get("/activities").json()
        assert "newuser@example.com" in all_activities[name]["participants"]

        # signup same user again -> should be rejected
        r2 = client.post(f"/activities/{name}/signup?email=newuser@example.com")
        assert r2.status_code == 400
        assert r2.json().get("detail") == "Student is already signed up"
    finally:
        remove_temp_activity(name)


def test_signup_respects_capacity():
    name = "Capacity Activity"
    # activity already has one participant and max_participants=1
    create_temp_activity(name, max_participants=1, participants=["only@x.com"])
    try:
        r = client.post(f"/activities/{name}/signup?email=another@example.com")
        assert r.status_code == 400
        assert r.json().get("detail") == "Activity is full"
    finally:
        remove_temp_activity(name)
