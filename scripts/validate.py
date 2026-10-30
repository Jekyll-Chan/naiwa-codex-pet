#!/usr/bin/env python3
"""Validate package geometry and real PNG alpha, plus installer behavior."""
import json
from pathlib import Path
import tempfile
from PIL import Image
from install import install, validate

root = Path(__file__).resolve().parents[1]
source = root / "pets" / "naiwa"
validate(source)
image = Image.open(source / "spritesheet.png").convert("RGBA")
assert image.size == (1536, 2288)
counts = [6, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8]
for row, count in enumerate(counts):
    for col in range(8):
        alpha = image.crop((col*192, row*208, (col+1)*192, (row+1)*208)).getchannel("A")
        assert (alpha.getbbox() is not None) == (col < count), (row, col)
        if col < count:
            assert alpha.getextrema() == (0, 255), (row, col, "missing transparent padding")
with tempfile.TemporaryDirectory() as tmp:
    pet_root = Path(tmp) / "pets"
    destination = install(source, pet_root)
    assert (destination / "pet.json").is_file()
    try:
        install(source, pet_root)
    except FileExistsError:
        pass
    else:
        raise AssertionError("Must refuse unintended replacement")
    install(source, pet_root, replace=True)
    validate(destination)
print(json.dumps({"ok": True, "version": 2, "frames": sum(counts), "installer": "verified"}))
