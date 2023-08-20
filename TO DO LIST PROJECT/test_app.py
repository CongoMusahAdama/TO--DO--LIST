from fastapi.testclient import TestClient
from .app import app

client= TestClient(app)

def test_read_app():
    response=client.get('/')
    assert response.status_code==200
    assert response.json()=={"msg":"hello you're there buddy!"}