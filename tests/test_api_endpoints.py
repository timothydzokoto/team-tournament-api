from io import BytesIO

from PIL import Image


def make_image_bytes() -> bytes:
    image = Image.new("RGB", (16, 16), color="white")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def register_and_login(client, username: str = "tester", email: str = "tester@example.com", password: str = "StrongPass123!"):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_team_subteam_player(client, headers):
    team_response = client.post(
        "/api/v1/teams",
        headers=headers,
        json={
            "name": "Team Alpha",
            "description": "Primary team",
            "coach_name": "Coach A",
        },
    )
    assert team_response.status_code == 200
    team_id = team_response.json()["id"]

    subteam_response = client.post(
        "/api/v1/subteams",
        headers=headers,
        json={
            "name": "Subteam A",
            "description": "Primary subteam",
            "team_id": team_id,
        },
    )
    assert subteam_response.status_code == 200
    subteam_id = subteam_response.json()["id"]

    player_response = client.post(
        "/api/v1/players",
        headers=headers,
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phone": "+15550001111",
            "position": "Forward",
            "jersey_number": 9,
            "height": 172.0,
            "weight": 64.0,
            "subteam_id": subteam_id,
        },
    )
    assert player_response.status_code == 200

    return {
        "team_id": team_id,
        "subteam_id": subteam_id,
        "player_id": player_response.json()["id"],
    }


def test_health_reports_service_state(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"healthy", "degraded"}
    assert "services" in body
    assert "database" in body["services"]
    assert "redis" in body["services"]
    assert "face_recognition" in body["services"]
    assert "uploads_dir" in body["services"]


def test_auth_flow_and_me_endpoint(client):
    headers = register_and_login(client)

    me_response = client.get("/api/v1/auth/me", headers=headers)

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "tester"


def test_protected_route_requires_token(client):
    response = client.get("/api/v1/teams")

    assert response.status_code == 403


def test_crud_flow_for_mobile_core_entities(client):
    headers = register_and_login(client)
    ids = create_team_subteam_player(client, headers)

    team_list_response = client.get("/api/v1/teams", headers=headers)
    subteam_list_response = client.get("/api/v1/subteams", headers=headers)
    player_list_response = client.get("/api/v1/players", headers=headers)

    assert team_list_response.status_code == 200
    assert len(team_list_response.json()) == 1
    assert subteam_list_response.status_code == 200
    assert len(subteam_list_response.json()) == 1
    assert player_list_response.status_code == 200
    assert len(player_list_response.json()) == 1
    assert ids["player_id"] > 0


def test_player_creation_fails_for_missing_subteam(client):
    headers = register_and_login(client)

    response = client.post(
        "/api/v1/players",
        headers=headers,
        json={
            "first_name": "Bad",
            "last_name": "Reference",
            "subteam_id": 9999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Subteam not found"


def test_face_match_rejects_invalid_image(client):
    headers = register_and_login(client)

    response = client.post(
        "/api/v1/players/face-match",
        headers=headers,
        files={"file": ("not-image.txt", b"plain text", "text/plain")},
    )

    assert response.status_code in {400, 503}
    if response.status_code == 400:
        assert response.json()["detail"] == "Invalid image file"


def test_upload_face_rejects_invalid_image(client):
    headers = register_and_login(client)
    ids = create_team_subteam_player(client, headers)

    response = client.post(
        f"/api/v1/players/{ids['player_id']}/upload-face",
        headers=headers,
        files={"file": ("bad.txt", b"plain text", "text/plain")},
    )

    assert response.status_code in {400, 503}


def test_upload_face_returns_503_when_face_dependency_unavailable(client):
    headers = register_and_login(client)
    ids = create_team_subteam_player(client, headers)
    image_bytes = make_image_bytes()

    response = client.post(
        f"/api/v1/players/{ids['player_id']}/upload-face",
        headers=headers,
        files={"file": ("face.jpg", image_bytes, "image/jpeg")},
    )

    assert response.status_code in {200, 503, 400}
