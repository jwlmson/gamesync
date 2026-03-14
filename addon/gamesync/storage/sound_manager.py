"""Sound asset file management — upload, validate, serve."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from gamesync.storage.db import Database
from gamesync.storage.models import SoundAsset, SoundCategory

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a"}


class SoundManager:
    """Manages sound asset files on disk + DB metadata."""

    def __init__(self, db: Database, data_path: str) -> None:
        self._db = db
        self._builtin_dir = Path(__file__).parent.parent / "sounds" / "builtin"
        self._custom_dir = Path(data_path) / "sounds" / "custom"
        self._custom_dir.mkdir(parents=True, exist_ok=True)

    @property
    def builtin_dir(self) -> Path:
        return self._builtin_dir

    @property
    def custom_dir(self) -> Path:
        return self._custom_dir

    def get_file_path(self, asset: SoundAsset) -> Path | None:
        """Resolve the full filesystem path for a sound asset."""
        if asset.category == SoundCategory.BUILT_IN:
            p = self._builtin_dir / asset.file_path
        else:
            p = self._custom_dir / asset.file_path
        return p if p.exists() else None

    async def upload(
        self, filename: str, data: bytes, name: str | None = None
    ) -> SoundAsset:
        """Upload a custom sound file. Returns the created SoundAsset."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}")

        if len(data) > MAX_UPLOAD_SIZE:
            raise ValueError(f"File too large ({len(data)} bytes). Max: {MAX_UPLOAD_SIZE}")

        # Sanitize filename
        safe_name = "".join(c for c in Path(filename).stem if c.isalnum() or c in "-_")
        if not safe_name:
            safe_name = "sound"

        # Deduplicate filename
        dest = self._custom_dir / f"{safe_name}{ext}"
        counter = 1
        while dest.exists():
            dest = self._custom_dir / f"{safe_name}_{counter}{ext}"
            counter += 1

        dest.write_bytes(data)

        asset = SoundAsset(
            name=name or safe_name,
            category=SoundCategory.CUSTOM,
            file_path=dest.name,
            file_size_bytes=len(data),
            duration_seconds=0.0,  # Could be computed with mutagen if added later
        )
        asset_id = await self._db.create_sound_asset(asset)
        asset.id = asset_id
        logger.info("Uploaded sound asset: %s (%d bytes)", asset.name, len(data))
        return asset

    async def delete(self, sound_id: int) -> bool:
        """Delete a custom sound asset (file + DB record)."""
        asset = await self._db.get_sound_asset(sound_id)
        if not asset:
            return False

        if asset.category == SoundCategory.BUILT_IN:
            raise ValueError("Cannot delete built-in sounds")

        # Remove file
        file_path = self._custom_dir / asset.file_path
        if file_path.exists():
            file_path.unlink()

        return await self._db.delete_sound_asset(sound_id)

    async def seed_builtin_sounds(self) -> int:
        """Register all built-in sound files in the DB. Returns count seeded."""
        if not self._builtin_dir.exists():
            logger.warning("Built-in sounds directory not found: %s", self._builtin_dir)
            return 0

        count = 0
        existing = await self._db.get_sound_assets(category=SoundCategory.BUILT_IN)
        existing_paths = {a.file_path for a in existing}

        for f in sorted(self._builtin_dir.iterdir()):
            if f.suffix.lower() in ALLOWED_EXTENSIONS and f.name not in existing_paths:
                asset = SoundAsset(
                    name=f.stem.replace("_", " ").replace("-", " ").title(),
                    category=SoundCategory.BUILT_IN,
                    file_path=f.name,
                    file_size_bytes=f.stat().st_size,
                )
                await self._db.create_sound_asset(asset)
                count += 1

        if count:
            logger.info("Seeded %d built-in sound assets", count)
        return count
