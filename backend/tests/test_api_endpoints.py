# Pytest tests for API endpoints 
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import ResearchRequest
from app.tasks import run_research_job
import time
from app.utils import get_db
from sqlalchemy.orm import Session
from app.db import SessionLocal

def get_test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  

@pytest.fixture(scope="module")
def test_db():
    return get_test_db()

client = TestClient(app)

@pytest.mark.asyncio
async def test_submit_research_success(test_db: Session):
    request = ResearchRequest(
        topic="Python programming basics",
        output_format="bullets"
    )
    response = await client.post("/research", json=request.model_dump())
    assert response.status_code == 200
    assert response.json()["job_id"] is not None    
    assert response.json()["status"] == "queued"

@pytest.mark.asyncio
async def test_submit_validation_fail(test_db: Session):
    response = await client.post("/research", json={"output_format": "bullets"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "field required"

@pytest.mark.asyncio
async def test_status_and_result_flow(test_db: Session):
    response = await client.post("/research", json={"topic": "Python programming basics", "output_format": "bullets"})
    assert response.status_code == 200
    assert response.json()["job_id"] is not None
    assert response.json()["status"] == "queued"    
    time.sleep(1)
    status_response = await client.get(f"/research/{response.json()['job_id']}/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "in_progress"
    result_response = await client.get(f"/research/{response.json()['job_id']}/result")
    assert result_response.status_code == 200
    assert result_response.json()["title"] is not None
    assert result_response.json()["summary"] is not None
    assert result_response.json()["conclusion"] is not None
    assert result_response.json()["output_format"] == "bullets"