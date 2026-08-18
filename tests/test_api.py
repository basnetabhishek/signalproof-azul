from fastapi.testclient import TestClient
from api import app

def test_health_and_home():
    client=TestClient(app)
    assert client.get("/health").json()=={"status":"ok"}
    assert client.get("/",follow_redirects=False).headers["location"]=="/index.html"
