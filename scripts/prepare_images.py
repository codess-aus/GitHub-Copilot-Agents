"""Copy only catalogue-listed uploads and create uncropped, efficient derivatives."""

import argparse
from pathlib import Path
import shutil

from PIL import Image, ImageOps
import yaml


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="Directory holding the exact listed source uploads.")
    args = parser.parse_args()
    chapters = yaml.safe_load((ROOT / "content" / "chapters.yml").read_text(encoding="utf-8"))
    image_root = ROOT / "docs" / "assets" / "images"
    for folder in ("originals", "heroes", "thumbnails"):
        (image_root / folder).mkdir(parents=True, exist_ok=True)
    for chapter in chapters:
        slug = chapter["slug"]
        original = image_root / "originals" / f"{slug}.png"
        if args.source_dir:
            source = args.source_dir / chapter["source_image"]
            if not source.is_file():
                raise FileNotFoundError(f"Required upload not found: {source}")
            shutil.copyfile(source, original)
        if not original.is_file():
            raise FileNotFoundError(f"Missing original {original}; supply --source-dir.")
        with Image.open(original) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            for folder, width, quality in (("heroes", 1672, 88), ("thumbnails", 640, 78)):
                resized = image.copy()
                resized.thumbnail((width, width), Image.Resampling.LANCZOS)
                resized.save(image_root / folder / f"{slug}.webp", quality=quality, method=6)
    print(f"Prepared {len(chapters)} originals, heroes and thumbnails (no cropping).")


if __name__ == "__main__":
    main()
