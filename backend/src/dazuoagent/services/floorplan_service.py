"""Floor-plan parsing utilities.

Real parsing is delegated to the agent (see `agent/agent.py`). This module
hosts the file-handling helpers — saving the upload, looking up the file
back later — so the agent layer doesn't have to know about disk paths.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from dazuoagent.core.config import settings


def save_upload(filename: str, content: bytes) -> Path:
    """Persist an uploaded file under `settings.upload_dir`.

    Returns the absolute path. Caller is responsible for recording this
    path on the project row.
    """
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix
    target = settings.upload_dir / f"{uuid.uuid4().hex}{suffix}"
    target.write_bytes(content)
    return target