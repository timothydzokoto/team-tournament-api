#!/usr/bin/env python3
"""
Simple test script for the Team Tournament API
Run this after starting the server to test basic functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("✅ Health check passed")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_auth():
    """Test authentication endpoints"""
    print("\n🔐 Testing authentication...")
    
    # Test registration
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=register_data)
    if response.status_code == 200:
        print("✅ User registration successful")
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None
    
    # Test login
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get("access_token")
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_teams(token):
    """Test team endpoints"""
    print("\n🏆 Testing team endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create team
    team_data = {
        "name": "Test Team",
        "description": "A test team for API testing",
        "coach_name": "Test Coach"
    }
    
    response = requests.post(f"{API_BASE}/teams", json=team_data, headers=headers)
    if response.status_code == 200:
        team = response.json()
        team_id = team["id"]
        print(f"✅ Team created with ID: {team_id}")
    else:
        print(f"❌ Team creation failed: {response.status_code} - {response.text}")
        return None
    
    # Get team
    response = requests.get(f"{API_BASE}/teams/{team_id}", headers=headers)
    if response.status_code == 200:
        print("✅ Team retrieval successful")
    else:
        print(f"❌ Team retrieval failed: {response.status_code}")
    
    # List teams
    response = requests.get(f"{API_BASE}/teams", headers=headers)
    if response.status_code == 200:
        teams = response.json()
        print(f"✅ Found {len(teams)} teams")
    else:
        print(f"❌ Team listing failed: {response.status_code}")
    
    return team_id

def test_subteams(token, team_id):
    """Test subteam endpoints"""
    print("\n👥 Testing subteam endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create subteam
    subteam_data = {
        "name": "Test Subteam",
        "description": "A test subteam",
        "team_id": team_id
    }
    
    response = requests.post(f"{API_BASE}/subteams", json=subteam_data, headers=headers)
    if response.status_code == 200:
        subteam = response.json()
        subteam_id = subteam["id"]
        print(f"✅ Subteam created with ID: {subteam_id}")
    else:
        print(f"❌ Subteam creation failed: {response.status_code} - {response.text}")
        return None
    
    # Get subteam
    response = requests.get(f"{API_BASE}/subteams/{subteam_id}", headers=headers)
    if response.status_code == 200:
        print("✅ Subteam retrieval successful")
    else:
        print(f"❌ Subteam retrieval failed: {response.status_code}")
    
    return subteam_id

def test_players(token, subteam_id):
    """Test player endpoints"""
    print("\n👤 Testing player endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create player
    player_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "position": "Forward",
        "jersey_number": 10,
        "height": 180.0,
        "weight": 75.0,
        "subteam_id": subteam_id
    }
    
    response = requests.post(f"{API_BASE}/players", json=player_data, headers=headers)
    if response.status_code == 200:
        player = response.json()
        player_id = player["id"]
        print(f"✅ Player created with ID: {player_id}")
    else:
        print(f"❌ Player creation failed: {response.status_code} - {response.text}")
        return None
    
    # Get player
    response = requests.get(f"{API_BASE}/players/{player_id}", headers=headers)
    if response.status_code == 200:
        print("✅ Player retrieval successful")
    else:
        print(f"❌ Player retrieval failed: {response.status_code}")
    
    # List players
    response = requests.get(f"{API_BASE}/players", headers=headers)
    if response.status_code == 200:
        players = response.json()
        print(f"✅ Found {len(players)} players")
    else:
        print(f"❌ Player listing failed: {response.status_code}")
    
    return player_id

def main():
    """Run all tests"""
    print("🚀 Starting Team Tournament API Tests")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("❌ Health check failed, stopping tests")
        return
    
    # Test authentication
    token = test_auth()
    if not token:
        print("❌ Authentication failed, stopping tests")
        return
    
    # Test teams
    team_id = test_teams(token)
    if not team_id:
        print("❌ Team tests failed, stopping tests")
        return
    
    # Test subteams
    subteam_id = test_subteams(token, team_id)
    if not subteam_id:
        print("❌ Subteam tests failed, stopping tests")
        return
    
    # Test players
    player_id = test_players(token, subteam_id)
    if not player_id:
        print("❌ Player tests failed")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    print(f"📊 Created: Team {team_id}, Subteam {subteam_id}, Player {player_id}")
    print(f"🔗 API Documentation: {BASE_URL}/docs")
    print(f"📖 ReDoc Documentation: {BASE_URL}/redoc")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server.")
        print("Make sure the server is running with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Test failed with error: {e}") 