import pytest
from fastapi.testclient import TestClient
import uuid
import os
from pathlib import Path
from app.core.config import settings

from app.main import app
from app.core.security import create_access_token
from app.models.user import User, RoleEnum

client = TestClient(app)

def _auth_header():
    token = create_access_token(data={"sub": "admin", "role": RoleEnum.ADMIN.value})
    return {"Authorization": f"Bearer {token}"}

def _mock_auth(monkeypatch):
    mock_user = User(id=1, username="admin", email="a@b.com",
                     hashed_password="fakehash", role=RoleEnum.ADMIN)
    monkeypatch.setattr("app.api.deps.get_user_by_username", lambda db, username: mock_user)

from app.crud import crud_evidence, crud_case
from app.schemas.evidence import EvidenceResponse
from datetime import datetime

def _mock_crud_case(monkeypatch):
    class MockCase:
        def __init__(self, case_id):
            self.case_id = case_id
    monkeypatch.setattr("app.crud.crud_case.get_case_by_case_id", lambda db, case_id: MockCase(case_id))

# Sample image bytes for testing
FAKE_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82"

def _mock_crud_create(monkeypatch):
    def mock_create(db, evidence_in):
        return EvidenceResponse(
            id=1,
            case_id=evidence_in.case_id,
            evidence_type=evidence_in.evidence_type,
            title=evidence_in.title,
            source=evidence_in.source,
            original_filename=evidence_in.original_filename,
            stored_filename=evidence_in.stored_filename,
            mime_type=evidence_in.mime_type,
            file_size=evidence_in.file_size,
            reference_path=evidence_in.reference_path,
            created_by=evidence_in.created_by,
            created_at=datetime.utcnow(),
            collected_at=datetime.utcnow()
        )
    monkeypatch.setattr(crud_evidence, "create_evidence", mock_create)

def test_evidence_metadata_only(monkeypatch):
    _mock_auth(monkeypatch)
    _mock_crud_create(monkeypatch)
    _mock_crud_case(monkeypatch)
    # Setup test case id
    case_id = f"TEST-CASE-{uuid.uuid4()}"

    # Post metadata-only evidence
    response = client.post(
        "/evidence/",
        headers=_auth_header(),
        data={
            "case_id": case_id,
            "evidence_type": "METADATA",
            "title": "Test Metadata Doc",
            "source": "NCRP"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case_id
    assert data["title"] == "Test Metadata Doc"
    assert data["original_filename"] is None

def test_evidence_file_upload_success(monkeypatch):
    _mock_auth(monkeypatch)
    _mock_crud_create(monkeypatch)
    _mock_crud_case(monkeypatch)


    case_id = f"TEST-CASE-{uuid.uuid4()}"

    # Upload an image
    files = {
        "file": ("test.png", FAKE_IMAGE_BYTES, "image/png")
    }
    data = {
        "case_id": case_id,
        "evidence_type": "IMAGE",
        "title": "Test Uploaded Image",
        "source": "Local"
    }

    response = client.post("/evidence/", headers=_auth_header(), data=data, files=files)
    assert response.status_code == 200
    res_data = response.json()

    assert res_data["title"] == "Test Uploaded Image"
    assert res_data["original_filename"] == "test.png"
    assert res_data["mime_type"] == "image/png"
    assert res_data["file_size"] == len(FAKE_IMAGE_BYTES)

    # Verify file exists on disk
    storage_dir = Path(settings.EVIDENCE_STORAGE_DIR)
    stored_path = storage_dir / res_data["reference_path"]
    assert stored_path.exists()
    assert stored_path.read_bytes() == FAKE_IMAGE_BYTES

    # Mock db.query for the download endpoint
    class MockQuery:
        def filter(self, *args):
            return self
        def first(self):
            from app.models.evidence import Evidence
            # Return a fake evidence model
            return Evidence(
                id=res_data["id"],
                case_id=case_id,
                original_filename="test.png",
                mime_type="image/png",
                reference_path=res_data["reference_path"]
            )

    monkeypatch.setattr("sqlalchemy.orm.Session.query", lambda self, *args: MockQuery())

    # Test download endpoint
    evidence_id = res_data["id"]
    download_res = client.get(f"/evidence/file/{evidence_id}", headers=_auth_header())
    assert download_res.status_code == 200
    assert download_res.content == FAKE_IMAGE_BYTES

    # Test cleanup
    stored_path.unlink()

def test_evidence_oversized_file(monkeypatch):
    _mock_auth(monkeypatch)
    _mock_crud_case(monkeypatch)
    case_id = f"TEST-CASE-{uuid.uuid4()}"

    # Since we can't easily send a 25MB+ payload efficiently in memory for this test,
    # we'll just mock a large file object if needed. However, since FastAPI `UploadFile`
    # handles files, we can simulate an oversized file by temporarily patching MAX_FILE_SIZE.
    import app.api.routes.evidence as ev_routes
    original_max = ev_routes.MAX_FILE_SIZE
    ev_routes.MAX_FILE_SIZE = 10  # 10 bytes max

    try:
        files = {
            "file": ("test.png", b"This string is longer than 10 bytes", "image/png")
        }
        data = {
            "case_id": case_id,
            "evidence_type": "IMAGE",
            "title": "Oversized",
        }

        response = client.post("/evidence/", headers=_auth_header(), data=data, files=files)
        assert response.status_code == 400
        assert "exceeds" in response.json()["detail"]
    finally:
        ev_routes.MAX_FILE_SIZE = original_max

def test_evidence_invalid_mime(monkeypatch):
    _mock_auth(monkeypatch)
    _mock_crud_case(monkeypatch)
    case_id = f"TEST-CASE-{uuid.uuid4()}"

    files = {
        "file": ("test.exe", b"executable_data", "application/x-msdownload")
    }
    data = {
        "case_id": case_id,
        "evidence_type": "OTHER",
        "title": "Invalid File",
    }

    response = client.post("/evidence/", headers=_auth_header(), data=data, files=files)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

def test_evidence_unauthenticated_upload():
    case_id = f"TEST-CASE-{uuid.uuid4()}"

    data = {
        "case_id": case_id,
        "evidence_type": "IMAGE",
        "title": "Unauth Upload",
    }
    response = client.post("/evidence/", data=data)
    assert response.status_code == 401

def test_evidence_unauthenticated_download():
    response = client.get("/evidence/file/9999")
    assert response.status_code == 401
