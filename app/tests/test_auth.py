import pytest
from app import app
from models import db, User
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_register(client):
    response = client.post('/register',
        data=json.dumps({
            'username': 'testuser',
            'password': 'testpass'
        }),
        content_type='application/json'
    )
    assert response.status_code == 201
    assert b'User created successfully' in response.data

def test_login(client):
    # First register a user
    client.post('/register',
        data=json.dumps({
            'username': 'testuser',
            'password': 'testpass'
        }),
        content_type='application/json'
    )
    
    # Then try to login
    response = client.post('/login',
        data=json.dumps({
            'username': 'testuser',
            'password': 'testpass'
        }),
        content_type='application/json'
    )
    assert response.status_code == 200
    assert 'token' in json.loads(response.data)

def test_invalid_login(client):
    response = client.post('/login',
        data=json.dumps({
            'username': 'wronguser',
            'password': 'wrongpass'
        }),
        content_type='application/json'
    )
    assert response.status_code == 401