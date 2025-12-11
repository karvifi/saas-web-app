"""
File upload/download capabilities for AI Agent Platform
Secure file handling, storage, and management
"""

import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, BinaryIO
from datetime import datetime, timedelta
import aiofiles
import asyncio
from fastapi import UploadFile, File, HTTPException, APIRouter, Depends, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import logging
import shutil
import magic  # python-magic for file type detection
from PIL import Image
import zipfile
import tempfile

logger = logging.getLogger(__name__)

class FileMetadata(BaseModel):
    """File metadata model"""
    file_id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    file_type: str  # image, document, video, audio, archive, etc.
    extension: str
    upload_date: datetime
    user_id: Optional[str]
    checksum: str
    storage_path: str
    public: bool = False
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

class FileStorage:
    """File storage management system"""

    def __init__(self, base_dir: str = "storage"):
        self.base_dir = Path(base_dir)
        self.uploads_dir = self.base_dir / "uploads"
        self.temp_dir = self.base_dir / "temp"
        self.thumbnails_dir = self.base_dir / "thumbnails"

        # Create directories
        for dir_path in [self.uploads_dir, self.temp_dir, self.thumbnails_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # File type categories
        self.file_categories = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
            'spreadsheet': ['.xls', '.xlsx', '.csv', '.ods'],
            'presentation': ['.ppt', '.pptx', '.odp'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php']
        }

        # Max file sizes (bytes)
        self.max_sizes = {
            'image': 10 * 1024 * 1024,      # 10MB
            'video': 100 * 1024 * 1024,     # 100MB
            'audio': 50 * 1024 * 1024,      # 50MB
            'document': 25 * 1024 * 1024,   # 25MB
            'other': 10 * 1024 * 1024       # 10MB
        }

        # In-memory file registry (in production, use database)
        self.file_registry: Dict[str, FileMetadata] = {}

    def _get_file_category(self, filename: str) -> str:
        """Get file category from filename"""
        ext = Path(filename).suffix.lower()
        for category, extensions in self.file_categories.items():
            if ext in extensions:
                return category
        return 'other'

    def _generate_file_id(self) -> str:
        """Generate unique file ID"""
        return str(uuid.uuid4())

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type using python-magic"""
        try:
            return magic.from_file(str(file_path), mime=True)
        except:
            return mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'

    def _validate_file(self, file_path: Path, original_filename: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        errors = []

        # Check file size
        file_size = file_path.stat().st_size
        category = self._get_file_category(original_filename)
        max_size = self.max_sizes.get(category, self.max_sizes['other'])

        if file_size > max_size:
            errors.append(f"File too large. Max size for {category} files: {max_size / 1024 / 1024:.1f}MB")

        # Check file type
        mime_type = self._get_mime_type(file_path)
        if not mime_type:
            errors.append("Could not determine file type")

        # Additional security checks
        if mime_type.startswith('text/html'):
            errors.append("HTML files not allowed")

        # Check for malicious content (basic)
        with open(file_path, 'rb') as f:
            header = f.read(512)
            if b'<script' in header.lower() or b'javascript:' in header.lower():
                errors.append("Potentially malicious content detected")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "file_size": file_size,
            "mime_type": mime_type,
            "category": category
        }

    async def save_upload(self, upload_file: UploadFile, user_id: Optional[str] = None,
                         public: bool = False, tags: List[str] = None) -> FileMetadata:
        """Save uploaded file"""
        file_id = self._generate_file_id()
        original_filename = upload_file.filename

        # Create storage path
        category = self._get_file_category(original_filename)
        storage_path = self.uploads_dir / category / f"{file_id}{Path(original_filename).suffix}"
        storage_path.parent.mkdir(exist_ok=True)

        # Save file temporarily for validation
        temp_path = self.temp_dir / f"temp_{file_id}"
        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)

            # Validate file
            validation = self._validate_file(temp_path, original_filename)
            if not validation["valid"]:
                temp_path.unlink()
                raise HTTPException(
                    status_code=400,
                    detail=f"File validation failed: {'; '.join(validation['errors'])}"
                )

            # Move to final location
            shutil.move(str(temp_path), str(storage_path))

            # Calculate checksum
            checksum = self._calculate_checksum(storage_path)

            # Create metadata
            metadata = FileMetadata(
                file_id=file_id,
                filename=storage_path.name,
                original_filename=original_filename,
                file_size=validation["file_size"],
                mime_type=validation["mime_type"],
                file_type=validation["category"],
                extension=Path(original_filename).suffix,
                upload_date=datetime.utcnow(),
                user_id=user_id,
                checksum=checksum,
                storage_path=str(storage_path),
                public=public,
                tags=tags or []
            )

            # Register file
            self.file_registry[file_id] = metadata

            # Generate thumbnail for images
            if validation["category"] == "image":
                await self._generate_thumbnail(storage_path, file_id)

            logger.info(f"File uploaded: {file_id} ({original_filename}) by user {user_id}")
            return metadata

        except Exception as e:
            # Clean up
            if temp_path.exists():
                temp_path.unlink()
            if storage_path.exists():
                storage_path.unlink()
            raise e

    async def _generate_thumbnail(self, file_path: Path, file_id: str, size: tuple = (200, 200)):
        """Generate thumbnail for image files"""
        try:
            thumbnail_path = self.thumbnails_dir / f"{file_id}_thumb.jpg"

            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", quality=85)

        except Exception as e:
            logger.warning(f"Failed to generate thumbnail for {file_id}: {e}")

    async def get_file(self, file_id: str, user_id: Optional[str] = None) -> Optional[FileMetadata]:
        """Get file metadata"""
        metadata = self.file_registry.get(file_id)
        if not metadata:
            return None

        # Check permissions
        if not metadata.public and metadata.user_id != user_id:
            return None

        return metadata

    async def download_file(self, file_id: str, user_id: Optional[str] = None) -> Optional[Path]:
        """Get file path for download"""
        metadata = await self.get_file(file_id, user_id)
        if not metadata:
            return None

        file_path = Path(metadata.storage_path)
        if not file_path.exists():
            return None

        return file_path

    async def delete_file(self, file_id: str, user_id: Optional[str] = None) -> bool:
        """Delete file"""
        metadata = await self.get_file(file_id, user_id)
        if not metadata:
            return False

        try:
            # Delete main file
            file_path = Path(metadata.storage_path)
            if file_path.exists():
                file_path.unlink()

            # Delete thumbnail if exists
            thumbnail_path = self.thumbnails_dir / f"{file_id}_thumb.jpg"
            if thumbnail_path.exists():
                thumbnail_path.unlink()

            # Remove from registry
            del self.file_registry[file_id]

            logger.info(f"File deleted: {file_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False

    async def list_user_files(self, user_id: str, file_type: Optional[str] = None,
                            tags: List[str] = None, public_only: bool = False) -> List[FileMetadata]:
        """List files for a user"""
        files = []
        for metadata in self.file_registry.values():
            if metadata.user_id != user_id:
                continue
            if public_only and not metadata.public:
                continue
            if file_type and metadata.file_type != file_type:
                continue
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
            files.append(metadata)

        return sorted(files, key=lambda x: x.upload_date, reverse=True)

    async def create_zip_archive(self, file_ids: List[str], user_id: str) -> Optional[str]:
        """Create ZIP archive from multiple files"""
        # Verify all files belong to user
        files_to_archive = []
        for file_id in file_ids:
            metadata = await self.get_file(file_id, user_id)
            if not metadata:
                raise HTTPException(status_code=404, detail=f"File {file_id} not found or access denied")
            files_to_archive.append(metadata)

        if not files_to_archive:
            return None

        # Create archive
        archive_id = self._generate_file_id()
        archive_path = self.temp_dir / f"archive_{archive_id}.zip"

        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for metadata in files_to_archive:
                file_path = Path(metadata.storage_path)
                zipf.write(file_path, metadata.original_filename)

        return str(archive_path)

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_files = len(self.file_registry)
        total_size = sum(m.file_size for m in self.file_registry.values())

        category_stats = {}
        for metadata in self.file_registry.values():
            cat = metadata.file_type
            if cat not in category_stats:
                category_stats[cat] = {"count": 0, "size": 0}
            category_stats[cat]["count"] += 1
            category_stats[cat]["size"] += metadata.file_size

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / 1024 / 1024,
            "categories": category_stats,
            "storage_dirs": {
                "uploads": str(self.uploads_dir),
                "temp": str(self.temp_dir),
                "thumbnails": str(self.thumbnails_dir)
            }
        }

# Global file storage instance
file_storage = FileStorage()

# FastAPI router for file operations
router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload", response_model=FileMetadata)
async def upload_file(
    file: UploadFile = File(...),
    public: bool = Query(False, description="Make file publicly accessible"),
    tags: str = Query("", description="Comma-separated tags"),
    user_id: str = Query(None, description="User ID (would come from auth)")
):
    """Upload a file"""
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    try:
        metadata = await file_storage.save_upload(
            upload_file=file,
            user_id=user_id,
            public=public,
            tags=tag_list
        )
        return metadata
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    user_id: str = Query(None, description="User ID (would come from auth)")
):
    """Download a file"""
    file_path = await file_storage.download_file(file_id, user_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type=file_storage._get_mime_type(file_path)
    )

@router.get("/thumbnail/{file_id}")
async def get_thumbnail(
    file_id: str,
    user_id: str = Query(None, description="User ID (would come from auth)")
):
    """Get file thumbnail"""
    metadata = await file_storage.get_file(file_id, user_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    if metadata.file_type != "image":
        raise HTTPException(status_code=400, detail="Thumbnails only available for images")

    thumbnail_path = file_storage.thumbnails_dir / f"{file_id}_thumb.jpg"
    if not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(
        path=thumbnail_path,
        media_type="image/jpeg"
    )

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    user_id: str = Query(None, description="User ID (would come from auth)")
):
    """Delete a file"""
    success = await file_storage.delete_file(file_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    return {"message": "File deleted successfully"}

@router.get("/list")
async def list_files(
    user_id: str = Query(..., description="User ID (would come from auth)"),
    file_type: str = Query(None, description="Filter by file type"),
    tags: str = Query("", description="Filter by tags (comma-separated)"),
    public_only: bool = Query(False, description="Only public files")
):
    """List user files"""
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    files = await file_storage.list_user_files(
        user_id=user_id,
        file_type=file_type,
        tags=tag_list,
        public_only=public_only
    )

    return {"files": files, "count": len(files)}

@router.post("/archive")
async def create_archive(
    file_ids: List[str],
    user_id: str = Query(..., description="User ID (would come from auth)")
):
    """Create ZIP archive from multiple files"""
    try:
        archive_path = await file_storage.create_zip_archive(file_ids, user_id)
        if not archive_path:
            raise HTTPException(status_code=400, detail="No files to archive")

        return FileResponse(
            path=archive_path,
            filename="archive.zip",
            media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats")
async def get_storage_stats():
    """Get storage statistics"""
    return file_storage.get_storage_stats()

@router.get("/info/{file_id}")
async def get_file_info(
    file_id: str,
    user_id: str = Query(None, description="User ID (would come from auth)")
):
    """Get file information"""
    metadata = await file_storage.get_file(file_id, user_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    return metadata

# Utility functions for agent file handling
async def save_agent_output_file(content: bytes, filename: str, user_id: str,
                               file_type: str = "document") -> str:
    """Save file generated by an agent"""
    file_id = file_storage._generate_file_id()
    category = file_type
    storage_path = file_storage.uploads_dir / category / f"{file_id}{Path(filename).suffix}"
    storage_path.parent.mkdir(exist_ok=True)

    async with aiofiles.open(storage_path, 'wb') as f:
        await f.write(content)

    # Create metadata
    checksum = file_storage._calculate_checksum(storage_path)
    mime_type = file_storage._get_mime_type(storage_path)

    metadata = FileMetadata(
        file_id=file_id,
        filename=storage_path.name,
        original_filename=filename,
        file_size=len(content),
        mime_type=mime_type,
        file_type=file_type,
        extension=Path(filename).suffix,
        upload_date=datetime.utcnow(),
        user_id=user_id,
        checksum=checksum,
        storage_path=str(storage_path),
        public=False,
        tags=["agent_generated"]
    )

    file_storage.file_registry[file_id] = metadata
    return file_id

async def get_agent_file_content(file_id: str, user_id: str) -> Optional[bytes]:
    """Get file content for agent processing"""
    file_path = await file_storage.download_file(file_id, user_id)
    if not file_path:
        return None

    async with aiofiles.open(file_path, 'rb') as f:
        return await f.read()

# Cleanup utilities
async def cleanup_temp_files():
    """Clean up old temporary files"""
    try:
        temp_dir = file_storage.temp_dir
        cutoff = datetime.utcnow() - timedelta(hours=1)

        for file_path in temp_dir.glob("*"):
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff:
                    file_path.unlink()
                    logger.info(f"Cleaned up temp file: {file_path.name}")

    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")

# Background cleanup task
async def start_file_cleanup_task():
    """Start background task to clean up old files"""
    while True:
        await cleanup_temp_files()
        await asyncio.sleep(3600)  # Clean up every hour