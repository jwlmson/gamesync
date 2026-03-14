"""Sound asset API — list, upload, delete, serve."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from gamesync.storage.models import SoundCategory

router = APIRouter(prefix="/sounds", tags=["sounds"])


class SoundAssetResponse(BaseModel):
    id: int
    name: str
    category: str
    file_path: str
    duration_seconds: float
    file_size_bytes: int


@router.get("", response_model=list[SoundAssetResponse])
async def list_sounds(category: str | None = Query(None)):
    from gamesync.main import db
    cat = SoundCategory(category) if category else None
    assets = await db.get_sound_assets(category=cat)
    return [
        SoundAssetResponse(
            id=a.id, name=a.name, category=a.category.value,
            file_path=a.file_path, duration_seconds=a.duration_seconds,
            file_size_bytes=a.file_size_bytes,
        )
        for a in assets
    ]


@router.get("/{sound_id}", response_model=SoundAssetResponse)
async def get_sound(sound_id: int):
    from gamesync.main import db
    asset = await db.get_sound_asset(sound_id)
    if not asset:
        raise HTTPException(404, "Sound not found")
    return SoundAssetResponse(
        id=asset.id, name=asset.name, category=asset.category.value,
        file_path=asset.file_path, duration_seconds=asset.duration_seconds,
        file_size_bytes=asset.file_size_bytes,
    )


@router.post("/upload", response_model=SoundAssetResponse)
async def upload_sound(
    file: UploadFile = File(...),
    name: str | None = Query(None),
):
    from gamesync.main import sound_manager
    if not sound_manager:
        raise HTTPException(500, "Sound manager not initialized")

    data = await file.read()
    try:
        asset = await sound_manager.upload(file.filename or "sound.mp3", data, name=name)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return SoundAssetResponse(
        id=asset.id, name=asset.name, category=asset.category.value,
        file_path=asset.file_path, duration_seconds=asset.duration_seconds,
        file_size_bytes=asset.file_size_bytes,
    )


@router.delete("/{sound_id}")
async def delete_sound(sound_id: int):
    from gamesync.main import sound_manager
    if not sound_manager:
        raise HTTPException(500, "Sound manager not initialized")
    try:
        deleted = await sound_manager.delete(sound_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not deleted:
        raise HTTPException(404, "Sound not found")
    return {"status": "deleted"}


@router.get("/{sound_id}/file")
async def serve_sound_file(sound_id: int):
    from gamesync.main import db, sound_manager
    if not sound_manager:
        raise HTTPException(500, "Sound manager not initialized")

    asset = await db.get_sound_asset(sound_id)
    if not asset:
        raise HTTPException(404, "Sound not found")

    file_path = sound_manager.get_file_path(asset)
    if not file_path:
        raise HTTPException(404, "Sound file not found on disk")

    return FileResponse(
        str(file_path),
        media_type="audio/mpeg",
        filename=file_path.name,
    )
