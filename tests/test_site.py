"""Check built output, reading order, local links and uncropped image derivatives."""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

from PIL import Image
import yaml


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CHAPTERS = yaml.safe_load((ROOT / "content" / "chapters.yml").read_text(encoding="utf-8"))
SITE_PREFIX = urlsplit(yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))["site_url"]).path


class PageParser(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self.images = []
        self.resources = []
        self.ids = set()
        self.h1_count = 0
        self.status_notice_count = 0
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a":
            self.anchors.append(attrs)
        if tag == "img":
            self.images.append(attrs)
        if tag in ("script", "link"):
            self.resources.append(attrs)
        if tag == "h1":
            self.h1_count += 1
        if "draft-notice" in attrs.get("class", "").split():
            self.status_notice_count += 1


def resolve_link(page, link):
    parts = urlsplit(link)
    if parts.scheme or parts.netloc:
        return None
    decoded_path = unquote(parts.path)
    if decoded_path.startswith(SITE_PREFIX):
        target = (SITE / decoded_path.removeprefix(SITE_PREFIX)).resolve()
    else:
        target = (page.parent / decoded_path).resolve() if decoded_path else page
    if target.is_dir():
        target /= "index.html"
    return target, unquote(parts.fragment)


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (SITE / "index.html").is_file():
            raise RuntimeError("Run python -m mkdocs build --strict before the tests.")
        cls.pages = {p.resolve(): PageParser(p) for p in SITE.rglob("*.html")}

    def test_all_chapters_and_overview(self):
        self.assertEqual(len(CHAPTERS), 28)
        home = self.pages[(SITE / "index.html").resolve()]
        cards = [a for a in home.anchors if "chapter-card" in a.get("class", "").split()]
        self.assertEqual(len(cards), len(CHAPTERS))
        for chapter, card in zip(CHAPTERS, cards):
            target, _ = resolve_link(SITE / "index.html", card["href"])
            self.assertEqual(target, (SITE / "chapters" / chapter["slug"] / "index.html").resolve())
        self.assertEqual(CHAPTERS[0]["slug"], "what-are-custom-agents")
        self.assertEqual(CHAPTERS[-1]["slug"], "architecture-summary")

    def test_reading_navigation(self):
        sequence = [SITE / "index.html"]
        sequence.extend(SITE / "chapters" / c["slug"] / "index.html" for c in CHAPTERS)
        sequence.append(SITE / "resources" / "index.html")
        for index, path in enumerate(sequence):
            page = self.pages[path.resolve()]
            with self.subTest(page=path):
                nav = [a for a in page.anchors if "reading-link" in a.get("class", "").split()]
                by_class = {c: a for a in nav for c in a["class"].split()}
                self.assertEqual(resolve_link(path, by_class["home"]["href"])[0], sequence[0].resolve())
                if index:
                    self.assertEqual(resolve_link(path, by_class["previous"]["href"])[0], sequence[index - 1].resolve())
                else:
                    self.assertNotIn("previous", by_class)
                if index < len(sequence) - 1:
                    self.assertEqual(resolve_link(path, by_class["next"]["href"])[0], sequence[index + 1].resolve())
                else:
                    self.assertNotIn("next", by_class)

    def test_internal_links_and_images(self):
        for path, page in self.pages.items():
            for attrs in [*page.anchors, *page.images, *page.resources]:
                link = attrs.get("href", attrs.get("src", ""))
                if not link:
                    continue
                with self.subTest(page=path, link=link):
                    target = resolve_link(path, link)
                    if target is None:
                        continue
                    destination, fragment = target
                    self.assertTrue(destination.is_relative_to(SITE.resolve()), link)
                    self.assertTrue(destination.is_file(), f"{path}: missing {link}")
                    if fragment and destination in self.pages:
                        self.assertIn(fragment, self.pages[destination].ids)

    def test_headings_alt_text_and_real_explanations(self):
        for chapter in CHAPTERS:
            path = SITE / "chapters" / chapter["slug"] / "index.html"
            page = self.pages[path.resolve()]
            self.assertEqual(page.h1_count, 1)
            self.assertGreaterEqual(len(re.findall(r"^## ", chapter["body"], re.MULTILINE)), 3)
            self.assertGreater(len(chapter["body"].split()), 100)
            self.assertTrue(any("original" in a.get("href", "") for a in page.anchors))
        for page in self.pages.values():
            for image in page.images:
                self.assertIn("alt", image)

    def test_image_aspect_ratio_and_thumbnail_budget(self):
        for chapter in CHAPTERS:
            image_root = ROOT / "docs" / "assets" / "images"
            slug = chapter["slug"]
            with Image.open(image_root / "originals" / f"{slug}.png") as original:
                expected_ratio = original.width / original.height
            for folder in ("heroes", "thumbnails"):
                path = image_root / folder / f"{slug}.webp"
                with Image.open(path) as derivative:
                    self.assertAlmostEqual(derivative.width / derivative.height, expected_ratio, delta=0.005)
                    if folder == "thumbnails":
                        self.assertLessEqual(derivative.width, 640)
                        self.assertLess(path.stat().st_size, 160_000)

    def test_publication_is_manual_and_confirmed(self):
        # BaseLoader retains the YAML key "on" instead of coercing it to a boolean.
        workflow = yaml.load((ROOT / ".github" / "workflows" / "pages.yml").read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(set(workflow["on"]), {"workflow_dispatch"})
        self.assertEqual(workflow["on"]["workflow_dispatch"]["inputs"]["publish"]["default"], "false")
        condition = workflow["jobs"]["deploy"]["if"]
        self.assertIn("inputs.publish", condition)
        self.assertIn("refs/heads/main", condition)

    def test_author_resources_are_rendered(self):
        config = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
        resources = config["extra"]["resources"]
        self.assertEqual(len(resources), 6)
        page = self.pages[(SITE / "resources" / "index.html").resolve()]
        links = {a.get("href") for a in page.anchors}
        for resource in resources:
            self.assertIn(resource["url"], links)
        self.assertNotIn("Resource collection coming soon", (SITE / "resources" / "index.html").read_text(encoding="utf-8"))

    def test_status_banner_matches_configuration(self):
        config = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
        expected = 1 if config["extra"].get("project_status") else 0
        for path, page in self.pages.items():
            if path.name == "404.html":
                continue
            with self.subTest(page=path):
                self.assertEqual(page.status_notice_count, expected)


if __name__ == "__main__":
    unittest.main()
