"""
Tests for Wellness Tracker App
"""

import pytest
import json
from app import app, db, User, WellnessReport
from datetime import date

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_create_user(client):
    """Test user creation"""
    response = client.post('/api/users', 
                          json={'username': 'testuser'},
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['username'] == 'testuser'
    assert 'id' in data

def test_create_duplicate_user(client):
    """Test creating duplicate user fails"""
    # Create first user
    client.post('/api/users', 
                json={'username': 'testuser'},
                content_type='application/json')
    
    # Try to create duplicate
    response = client.post('/api/users', 
                          json={'username': 'testuser'},
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'already exists' in data['error']

def test_submit_wellness_report(client):
    """Test submitting wellness report"""
    # Create user first
    user_response = client.post('/api/users', 
                               json={'username': 'testuser'},
                               content_type='application/json')
    user_data = json.loads(user_response.data)
    user_id = user_data['id']
    
    # Submit wellness report
    report_data = {
        'mood_score': 8,
        'energy_level': 7,
        'sleep_quality': 6,
        'stress_level': 4,
        'physical_symptoms': 'Feeling good today'
    }
    
    response = client.post(f'/api/users/{user_id}/reports',
                          json=report_data,
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'wellness_score' in data
    assert 'ai_insights' in data
    assert data['wellness_score'] > 0

def test_wellness_score_calculation():
    """Test wellness score calculation logic"""
    from app import calculate_wellness_score
    
    # Test high wellness scores
    high_wellness_data = {
        'mood_score': 9,
        'energy_level': 8,
        'sleep_quality': 9,
        'stress_level': 2
    }
    score = calculate_wellness_score(high_wellness_data)
    assert score > 80  # Should be high score
    
    # Test low wellness scores
    low_wellness_data = {
        'mood_score': 3,
        'energy_level': 2,
        'sleep_quality': 3,
        'stress_level': 9
    }
    score = calculate_wellness_score(low_wellness_data)
    assert score < 40  # Should be low score

def test_get_wellness_reports(client):
    """Test getting wellness reports"""
    # Create user and submit report
    user_response = client.post('/api/users', 
                               json={'username': 'testuser'},
                               content_type='application/json')
    user_data = json.loads(user_response.data)
    user_id = user_data['id']
    
    report_data = {
        'mood_score': 8,
        'energy_level': 7,
        'sleep_quality': 6,
        'stress_level': 4
    }
    
    client.post(f'/api/users/{user_id}/reports',
                json=report_data,
                content_type='application/json')
    
    # Get reports
    response = client.get(f'/api/users/{user_id}/reports')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['mood_score'] == 8

def test_wellness_summary(client):
    """Test wellness summary endpoint"""
    # Create user and submit report
    user_response = client.post('/api/users', 
                               json={'username': 'testuser'},
                               content_type='application/json')
    user_data = json.loads(user_response.data)
    user_id = user_data['id']
    
    report_data = {
        'mood_score': 8,
        'energy_level': 7,
        'sleep_quality': 6,
        'stress_level': 4
    }
    
    client.post(f'/api/users/{user_id}/reports',
                json=report_data,
                content_type='application/json')
    
    # Get summary
    response = client.get(f'/api/users/{user_id}/wellness-summary')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'average_wellness_score' in data
    assert 'averages' in data
    assert data['total_reports'] == 1

def test_ai_insights_generation():
    """Test AI insights generation"""
    from app import generate_ai_insights
    
    # Test with symptoms
    insights = generate_ai_insights("I have a headache and feel tired")
    assert "focus on sleep" in insights.lower() or "hydrated" in insights.lower()
    
    # Test with empty symptoms
    insights = generate_ai_insights("")
    assert "No significant symptoms" in insights

def test_missing_required_fields(client):
    """Test validation of required fields"""
    user_response = client.post('/api/users', 
                               json={'username': 'testuser'},
                               content_type='application/json')
    user_data = json.loads(user_response.data)
    user_id = user_data['id']
    
    # Submit report with missing fields
    incomplete_data = {
        'mood_score': 8,
        # Missing energy_level, sleep_quality, stress_level
    }
    
    response = client.post(f'/api/users/{user_id}/reports',
                          json=incomplete_data,
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'required' in data['error']

if __name__ == '__main__':
    pytest.main([__file__])