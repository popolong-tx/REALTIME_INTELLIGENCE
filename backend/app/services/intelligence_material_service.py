"""Isolated third-party material ingestion for institutional research sessions."""

from __future__ import annotations

from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
from xml.etree import ElementTree
from zipfile import ZipFile, BadZipFile

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.intelligence_monitoring import IntelligenceMaterial


ALLOWED_MATERIAL_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
    ".html": "text/html",
    ".htm": "text/html",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


class MaterialNotFoundError(LookupError):
    pass


class MaterialValidationError(ValueError):
    pass


class IntelligenceMaterialService:
    """Persist and read materials with session and workspace isolation."""

    def __init__(self) -> None:
        self.storage_dir = Path(settings.INTELLIGENCE_MATERIALS_DIR)

    @staticmethod
    def _safe_filename(filename: str) -> str:
        value = Path(filename or "material").name
        value = re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff ]+", "_", value).strip(" .")
        return (value or "material")[:180]

    @staticmethod
    def _session_key(session_id: str) -> str:
        return sha256(session_id.encode("utf-8")).hexdigest()[:32]

    def _path(self, workspace_id: str, session_id: str, material_id: str, filename: str) -> Path:
        workspace_key = sha256(workspace_id.encode("utf-8")).hexdigest()[:20]
        return self.storage_dir / workspace_key / self._session_key(session_id) / f"{material_id}-{self._safe_filename(filename)}"

    @staticmethod
    def _extension(filename: str) -> str:
        return Path(filename or "").suffix.lower()

    @staticmethod
    def _validate_signature(extension: str, payload: bytes) -> None:
        signatures = {
            ".pdf": payload.startswith(b"%PDF-"),
            ".png": payload.startswith(b"\x89PNG\r\n\x1a\n"),
            ".jpg": payload.startswith(b"\xff\xd8\xff"),
            ".jpeg": payload.startswith(b"\xff\xd8\xff"),
            ".webp": payload[:4] == b"RIFF" and payload[8:12] == b"WEBP",
            ".docx": payload.startswith(b"PK\x03\x04"),
        }
        if extension in signatures and not signatures[extension]:
            raise MaterialValidationError("文件内容与扩展名不匹配，已拒绝上传")

    @staticmethod
    def _extract_docx(path: Path) -> str:
        try:
            with ZipFile(path) as archive:
                xml = archive.read("word/document.xml")
            root = ElementTree.fromstring(xml)
        except (BadZipFile, KeyError, ElementTree.ParseError) as exc:
            raise MaterialValidationError("DOCX 文件结构无法解析") from exc
        paragraphs = []
        for paragraph in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
            text = "".join(node.text or "" for node in paragraph.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"))
            if text.strip():
                paragraphs.append(text.strip())
        return "\n".join(paragraphs)

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
        except Exception as exc:
            raise MaterialValidationError("PDF 文本解析失败；扫描型 PDF 请改用截图或启用 OCR") from exc

    @staticmethod
    def _extract_text(path: Path, content_type: str) -> str:
        if path.suffix.lower() == ".pdf":
            return IntelligenceMaterialService._extract_pdf(path)
        if path.suffix.lower() == ".docx":
            return IntelligenceMaterialService._extract_docx(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        if content_type == "text/html":
            text = re.sub(r"<[^>]+>", " ", text)
            text = unescape(text)
        if path.suffix.lower() == ".json":
            try:
                text = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    def create_session(self, workspace_id: str) -> Dict[str, Any]:
        session_id = str(uuid4())
        return {"session_id": session_id, "workspace_id": workspace_id, "isolation": "session_scoped"}

    async def ingest(
        self,
        db: Session,
        *,
        session_id: str,
        workspace_id: str,
        upload: UploadFile,
    ) -> IntelligenceMaterial:
        filename = self._safe_filename(upload.filename or "material")
        extension = self._extension(filename)
        content_type = ALLOWED_MATERIAL_TYPES.get(extension)
        if not content_type:
            raise MaterialValidationError("不支持的文件类型；支持 PDF、DOCX、TXT、Markdown、CSV、JSON、HTML 和 PNG/JPEG/WebP")
        existing_count = db.query(IntelligenceMaterial).filter(
            IntelligenceMaterial.session_id == session_id,
            IntelligenceMaterial.workspace_id == workspace_id,
        ).count()
        if existing_count >= settings.INTELLIGENCE_MATERIAL_MAX_COUNT:
            raise MaterialValidationError("单个研究会话最多上传 30 份资料")

        payload = await upload.read(settings.INTELLIGENCE_MATERIAL_MAX_BYTES + 1)
        if len(payload) > settings.INTELLIGENCE_MATERIAL_MAX_BYTES:
            raise MaterialValidationError("单个文件超过 25 MB 限制")
        self._validate_signature(extension, payload)
        material_id = str(uuid4())
        final_path = self._path(workspace_id, session_id, material_id, filename)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        final_path.write_bytes(payload)
        digest = sha256(payload).hexdigest()
        extracted_text = None
        status = "image_ready" if content_type in IMAGE_TYPES else "ready"
        error = None
        if content_type not in IMAGE_TYPES:
            try:
                extracted_text = self._extract_text(final_path, content_type)
            except MaterialValidationError as exc:
                status = "extraction_failed"
                error = str(exc)
        material = IntelligenceMaterial(
            id=material_id,
            session_id=session_id,
            workspace_id=workspace_id,
            filename=filename,
            content_type=content_type,
            byte_size=len(payload),
            sha256=digest,
            storage_path=str(final_path),
            extracted_text=extracted_text,
            extraction_status=status,
            extraction_error=error,
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        return material

    def list_materials(self, db: Session, *, session_id: str, workspace_id: str) -> List[IntelligenceMaterial]:
        return db.query(IntelligenceMaterial).filter(
            IntelligenceMaterial.session_id == session_id,
            IntelligenceMaterial.workspace_id == workspace_id,
        ).order_by(IntelligenceMaterial.created_at.asc()).all()

    def get_material(self, db: Session, material_id: str, *, session_id: str, workspace_id: str) -> IntelligenceMaterial:
        material = db.query(IntelligenceMaterial).filter(
            IntelligenceMaterial.id == material_id,
            IntelligenceMaterial.session_id == session_id,
            IntelligenceMaterial.workspace_id == workspace_id,
        ).first()
        if not material:
            raise MaterialNotFoundError(material_id)
        return material

    @staticmethod
    def serialize(material: IntelligenceMaterial) -> Dict[str, Any]:
        return {
            "id": material.id,
            "session_id": material.session_id,
            "workspace_id": material.workspace_id,
            "filename": material.filename,
            "content_type": material.content_type,
            "byte_size": material.byte_size,
            "sha256": material.sha256,
            "extraction_status": material.extraction_status,
            "extraction_error": material.extraction_error,
            "text_characters": len(material.extracted_text or ""),
            "created_at": material.created_at.isoformat() + "Z" if material.created_at else None,
        }

    def analysis_inputs(self, db: Session, *, session_id: str, workspace_id: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        materials = self.list_materials(db, session_id=session_id, workspace_id=workspace_id)
        text_inputs = []
        image_inputs = []
        for material in materials:
            if material.extracted_text:
                text_inputs.append({"material_id": material.id, "filename": material.filename, "text": material.extracted_text[:120_000]})
            elif material.content_type in IMAGE_TYPES:
                image_inputs.append({
                    "material_id": material.id,
                    "filename": material.filename,
                    "content_type": material.content_type,
                    "data_url": f"data:{material.content_type};base64,{b64encode(Path(material.storage_path).read_bytes()).decode('ascii')}",
                })
        return text_inputs, image_inputs


intelligence_material_service = IntelligenceMaterialService()
