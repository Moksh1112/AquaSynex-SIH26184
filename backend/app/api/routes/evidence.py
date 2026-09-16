from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil
from pathlib import Path
from app.db.session import get_db
from app.schemas.evidence import EvidenceCreate, EvidenceResponse
from app.crud import crud_evidence, crud_audit
from app.schemas.audit import AuditLogCreate
from app.api.deps import get_current_user, require_role
from app.models.user import User, RoleEnum
from app.core.config import settings

_any_role = require_role(
    RoleEnum.ADMIN.value,
    RoleEnum.I4C_ANALYST.value,
    RoleEnum.LEA_INVESTIGATOR.value,
    RoleEnum.BANK_OFFICER.value
)

router = APIRouter(prefix="/evidence")

ALLOWED_MIME_TYPES = {
    "application/pdf", "text/plain", "text/csv",
    "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg", "image/png", "video/mp4", "video/webm"
}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

@router.post("/", response_model=EvidenceResponse)
async def create_evidence(
    case_id: str = Form(...),
    evidence_type: str = Form(...),
    title: str = Form(...),
    source: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(_any_role)
):
    user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)

    # Verify case exists (RBAC check)
    from app.crud.crud_case import get_case_by_case_id
    if not get_case_by_case_id(db, case_id=case_id):
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    evidence_in = EvidenceCreate(
        case_id=case_id,
        evidence_type=evidence_type,
        title=title,
        source=source,
        created_by=user_role
    )

    file_path = None
    if file and file.filename:
        # Validate MIME type (basic check from content_type)
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

        # Validate file size
        file.file.seek(0, 2) # seek to end
        file_size = file.file.tell()
        file.file.seek(0) # seek back to start

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds the 25 MB limit.")

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty files are not allowed.")

        # Setup storage
        storage_dir = Path(settings.EVIDENCE_STORAGE_DIR) / case_id
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Generate safe filename
        ext = os.path.splitext(file.filename)[1]
        stored_filename = f"{uuid.uuid4()}{ext}"
        file_path = storage_dir / stored_filename

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to save file to disk.")

        # Update metadata
        evidence_in.original_filename = file.filename
        evidence_in.stored_filename = stored_filename
        evidence_in.mime_type = file.content_type
        evidence_in.file_size = file_size
        evidence_in.reference_path = f"{case_id}/{stored_filename}"

    try:
        created_evidence = crud_evidence.create_evidence(db, evidence_in)
    except Exception as e:
        # Rollback physical file if DB creation fails
        if file_path and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail="Database error occurred.")

    try:
        # Create single audit log with correct authenticated user_id
        user_id = current_user.id
        audit_log = AuditLogCreate(
            user_id=user_id,
            action="EVIDENCE_ADDED",
            resource=f"evidence:{created_evidence.id}",
            status="SUCCESS"
        )
        crud_audit.create_audit_log(db, audit_log)
    except Exception:
        # If audit log fails, evidence is already created and file is saved, so we do not rollback.
        pass

    return created_evidence

@router.get("/{case_id}", response_model=List[EvidenceResponse])
def get_evidence_for_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(_any_role)
):
    # Verify case exists (RBAC check)
    from app.crud.crud_case import get_case_by_case_id
    if not get_case_by_case_id(db, case_id=case_id):
        raise HTTPException(status_code=404, detail="Case not found or access denied")

    return crud_evidence.get_evidence_by_case(db, case_id)

@router.get("/file/{evidence_id}")
def download_evidence_file(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_any_role)
):
    # Fetch evidence record to ensure user has access (RBAC logic applies)
    from app.models.evidence import Evidence
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found.")

    # Verify case exists and user has access to this evidence's case
    from app.crud.crud_case import get_case_by_case_id
    if not get_case_by_case_id(db, case_id=evidence.case_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this case's evidence")

    if not evidence.reference_path or not evidence.original_filename:
        raise HTTPException(status_code=404, detail="This evidence record does not have an associated file.")

    storage_dir = Path(settings.EVIDENCE_STORAGE_DIR)
    file_path = storage_dir / evidence.reference_path

    # Path traversal protection - ensure the resolved path is within the storage directory
    try:
        resolved_path = file_path.resolve(strict=True)
        resolved_storage = storage_dir.resolve(strict=True)
        if not str(resolved_path).startswith(str(resolved_storage)):
            raise ValueError("Path traversal attempt")
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=404, detail="File not found on disk.")

    return FileResponse(
        path=resolved_path,
        filename=evidence.original_filename,
        media_type=evidence.mime_type or "application/octet-stream",
        content_disposition_type="attachment"
    )
