import os
from pathlib import Path


def read_env_or_file(name: str, default: str | None = None) -> str | None:
    direct = os.getenv(name)
    if direct is not None and direct.strip():
        return direct.strip()

    file_var = os.getenv(f"{name}_FILE")
    if file_var and file_var.strip():
        value = Path(file_var.strip()).read_text(encoding="utf-8").strip()
        if value:
            return value

    return default
