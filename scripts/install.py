#!/usr/bin/env python3
"""Install the bundled Naiwa pet locally. Python 3.9+, no dependencies/network."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile

EXPECTED_SHA256 = "bf0b120f79783a7ded7e80b5c747760576e161637a8c831f8e790a4735c085f7"


def validate(source):
    data = (source / "spritesheet.png").read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Sprite checksum mismatch; download the official package again.")
    if data[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", data[16:24]) != (1536, 2288):
        raise ValueError("Expected the 1536 x 2288 v2 PNG sprite sheet.")
    manifest = json.loads((source / "pet.json").read_text(encoding="utf-8"))
    if (manifest.get("id"), manifest.get("spriteVersionNumber"), manifest.get("spritesheetPath")) != ("naiwa", 2, "spritesheet.png"):
        raise ValueError("Unexpected pet manifest.")


def install(source, pet_root, replace=False):
    validate(source)
    destination = pet_root / "naiwa"
    if destination.exists() and not replace:
        raise FileExistsError(f"Already installed: {destination}. Use --replace to update.")
    pet_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".naiwa-", dir=pet_root) as tmp:
        staged = Path(tmp) / "naiwa"
        shutil.copytree(source, staged)
        backup = Path(tmp) / "previous"
        if destination.exists():
            destination.rename(backup)
        try:
            staged.rename(destination)
        except Exception:
            if backup.exists():
                backup.rename(destination)
            raise
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, help="Override CODEX_HOME for a custom installation.")
    parser.add_argument("--replace", action="store_true", help="Replace an existing Naiwa installation.")
    parser.add_argument("--check", action="store_true", help="Verify package integrity without writing files.")
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / "pets" / "naiwa"
    try:
        if args.check:
            validate(source)
            print("Naiwa package integrity: OK")
            return
        codex_home = args.codex_home or Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        destination = install(source, codex_home.expanduser() / "pets", args.replace)
    except (ValueError, FileExistsError, OSError) as exc:
        parser.exit(1, f"Installation stopped: {exc}\n")
    print(f"Installed Naiwa: {destination}\nOpen Settings > Pets, refresh, and select 奶蛙 Naiwa.\nUse /pet to show the desktop companion.")


if __name__ == "__main__":
    main()
