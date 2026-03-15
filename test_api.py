#!/usr/bin/env python3
"""
Simple test script for the Team Tournament API.
Run this after starting the server to test basic functionality.
"""

import time
import requests

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

_RUN_SUFFIX = str(int(time.time()))
TEST_USERNAME = f"testuser_{_RUN_SUFFIX}"
TEST_EMAIL = f"{TEST_USERNAME}@example.com"
TEST_PASSWORD = "testpassword123"


def test_health() -> bool:
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("PASS: Health check passed")
        return True

    print(f"FAIL: Health check failed: {response.status_code}")
    return False


def test_auth() -> str | None:
    """Test authentication endpoints and return access token."""
    print("\nTesting authentication...")

    register_data = {
        "username": TEST_USERNAME,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    }

    response = requests.post(f"{API_BASE}/auth/register", json=register_data)
    if response.status_code == 200:
        print("PASS: User registration successful")
    else:
        print(f"FAIL: Registration failed: {response.status_code} - {response.text}")
        return None

    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
    }

    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("PASS: Login successful")
        return token

    print(f"FAIL: Login failed: {response.status_code} - {response.text}")
    return None


def test_teams(token: str) -> int | None:
    """Test team endpoints and return team id."""
    print("\nTesting team endpoints...")
    headers = {"Authorization": f"Bearer {token}"}

    team_data = {
        "name": f"Test Team {_RUN_SUFFIX}",
        "description": "A test team for API testing",
        "coach_name": "Test Coach",
    }

    response = requests.post(f"{API_BASE}/teams", json=team_data, headers=headers)
    if response.status_code == 200:
        team_id = response.json()["id"]
        print(f"PASS: Team created with ID: {team_id}")
    else:
        print(f"FAIL: Team creation failed: {response.status_code} - {response.text}")
        return None

    response = requests.get(f"{API_BASE}/teams/{team_id}", headers=headers)
    if response.status_code == 200:
        print("PASS: Team retrieval successful")
    else:
        print(f"FAIL: Team retrieval failed: {response.status_code}")

    response = requests.get(f"{API_BASE}/teams", headers=headers)
    if response.status_code == 200:
        teams = response.json()
        print(f"PASS: Found {len(teams)} teams")
    else:
        print(f"FAIL: Team listing failed: {response.status_code}")

    return team_id


def test_subteams(token: str, team_id: int) -> int | None:
    """Test subteam endpoints and return subteam id."""
    print("\nTesting subteam endpoints...")
    headers = {"Authorization": f"Bearer {token}"}

    subteam_data = {
        "name": f"Test Subteam {_RUN_SUFFIX}",
        "description": "A test subteam",
        "team_id": team_id,
    }

    response = requests.post(f"{API_BASE}/subteams", json=subteam_data, headers=headers)
    if response.status_code == 200:
        subteam_id = response.json()["id"]
        print(f"PASS: Subteam created with ID: {subteam_id}")
    else:
        print(f"FAIL: Subteam creation failed: {response.status_code} - {response.text}")
        return None

    response = requests.get(f"{API_BASE}/subteams/{subteam_id}", headers=headers)
    if response.status_code == 200:
        print("PASS: Subteam retrieval successful")
    else:
        print(f"FAIL: Subteam retrieval failed: {response.status_code}")

    return subteam_id


def test_players(token: str, subteam_id: int) -> int | None:
    """Test player endpoints and return player id."""
    print("\nTesting player endpoints...")
    headers = {"Authorization": f"Bearer {token}"}

    player_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": f"john.doe.{_RUN_SUFFIX}@example.com",
        "phone": "+1234567890",
        "position": "Forward",
        "jersey_number": 10,
        "height": 180.0,
        "weight": 75.0,
        "subteam_id": subteam_id,
    }

    response = requests.post(f"{API_BASE}/players", json=player_data, headers=headers)
    if response.status_code == 200:
        player_id = response.json()["id"]
        print(f"PASS: Player created with ID: {player_id}")
    else:
        print(f"FAIL: Player creation failed: {response.status_code} - {response.text}")
        return None

    response = requests.get(f"{API_BASE}/players/{player_id}", headers=headers)
    if response.status_code == 200:
        print("PASS: Player retrieval successful")
    else:
        print(f"FAIL: Player retrieval failed: {response.status_code}")

    response = requests.get(f"{API_BASE}/players", headers=headers)
    if response.status_code == 200:
        players = response.json()
        print(f"PASS: Found {len(players)} players")
    else:
        print(f"FAIL: Player listing failed: {response.status_code}")

    return player_id


def main() -> None:
    """Run all tests."""
    print("Starting Team Tournament API Tests")
    print("=" * 50)
    print(f"Using test account: {TEST_USERNAME}")

    if not test_health():
        print("FAIL: Health check failed, stopping tests")
        return

    token = test_auth()
    if not token:
        print("FAIL: Authentication failed, stopping tests")
        return

    team_id = test_teams(token)
    if not team_id:
        print("FAIL: Team tests failed, stopping tests")
        return

    subteam_id = test_subteams(token, team_id)
    if not subteam_id:
        print("FAIL: Subteam tests failed, stopping tests")
        return

    player_id = test_players(token, subteam_id)
    if not player_id:
        print("FAIL: Player tests failed")
        return

    print("\n" + "=" * 50)
    print("PASS: All tests completed successfully!")
    print(f"Created: Team {team_id}, Subteam {subteam_id}, Player {player_id}")
    print(f"API Documentation: {BASE_URL}/docs")
    print(f"ReDoc Documentation: {BASE_URL}/redoc")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("FAIL: Could not connect to the API server.")
        print("Make sure the server is running with: uvicorn app.main:app --reload")
    except Exception as exc:
        print(f"FAIL: Test failed with error: {exc}")
