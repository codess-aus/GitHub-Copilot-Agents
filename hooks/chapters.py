"""Generate chapters, navigation and image metadata from one ordered catalogue."""

from pathlib import Path
import re
from urllib.parse import urlparse

from mkdocs.exceptions import PluginError
from mkdocs.structure.files import File
import yaml
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "content" / "chapters.yml"
CHAPTERS = []


def on_config(config):
    global CHAPTERS
    CHAPTERS = yaml.safe_load(CATALOGUE.read_text(encoding="utf-8"))
    if not isinstance(CHAPTERS, list) or not CHAPTERS:
        raise PluginError("content/chapters.yml must contain a non-empty chapter list.")
    seen = set()
    for number, chapter in enumerate(CHAPTERS, 1):
        for field in ("slug", "title", "summary", "body", "source_image"):
            if not isinstance(chapter.get(field), str) or not chapter[field].strip():
                raise PluginError(f"Chapter {number}: missing or empty {field}.")
        slug = chapter["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug in seen:
            raise PluginError(f"Invalid or duplicate chapter slug: {slug}")
        seen.add(slug)
        chapter["number"] = number
        chapter["path"] = f"chapters/{slug}.md"
        chapter["original"] = f"assets/images/originals/{slug}.png"
        chapter["hero"] = f"assets/images/heroes/{slug}.webp"
        chapter["thumbnail"] = f"assets/images/thumbnails/{slug}.webp"
        for field in ("original", "hero", "thumbnail"):
            image = Path(config.docs_dir) / chapter[field]
            if not image.is_file():
                raise PluginError(f"Missing {field}: {image}. Run scripts/prepare_images.py.")
        with Image.open(Path(config.docs_dir) / chapter["original"]) as image:
            chapter["width"], chapter["height"] = image.size
    extras = config.extra
    urls = [extras.get("blog_url", "")]
    urls += [item.get("link", "") for item in extras.get("social", [])]
    urls += [item.get("url", "") for item in extras.get("resources", [])]
    for url in filter(None, urls):
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise PluginError(f"External destinations must be complete HTTPS URLs: {url}")
    config.nav = [
        {"Home": "index.md"},
        {"Chapters": [{f'{c["number"]:02d}. {c["title"]}': c["path"]} for c in CHAPTERS]},
        {"Resources": "resources.md"},
    ]
    return config


def on_files(files, config):
    for chapter in CHAPTERS:
        content = f'# {chapter["title"]}\n\n{chapter["summary"]}\n\n{chapter["body"]}\n'
        generated = File.generated(config, chapter["path"], content=content)
        chapter["url"] = generated.url
        files.append(generated)
    return files


def on_page_context(context, page, config, nav):
    pages = [{"title": "Home", "path": "index.md", "url": "."}, *CHAPTERS,
             {"title": "Resources", "path": "resources.md", "url": "resources/"}]
    current = next((i for i, p in enumerate(pages) if p["path"] == page.file.src_uri), None)
    context["catalogue"] = CHAPTERS
    context["chapter"] = next((c for c in CHAPTERS if c["path"] == page.file.src_uri), None)
    context["is_home"] = page.file.src_uri == "index.md"
    context["is_resources"] = page.file.src_uri == "resources.md"
    context["reading_previous"] = pages[current - 1] if current is not None and current > 0 else None
    context["reading_next"] = pages[current + 1] if current is not None and current < len(pages) - 1 else None
    return context
