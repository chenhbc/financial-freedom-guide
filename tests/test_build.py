"""Build checks: pages exist, prose is intact, chart numbers come from the essays."""
from __future__ import annotations

import html
import re
import sys
import unittest
from pathlib import Path
from urllib.parse import unquote, urljoin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "site"))

import build  # noqa: E402

TOKEN = re.compile(r"\d[\d,]*(?:\.\d+)?%?")
BLOCK = re.compile(
    r"<(p|li|h1|h2|h3|blockquote|figcaption|td|th|cite)\b[^>]*>(.*?)</\1>",
    re.S,
)
SVG_TEXT = re.compile(r"<text\b[^>]*>(.*?)</text>", re.S)


def visible(fragment: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", fragment, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def blocks(fragment: str) -> list[str]:
    cleaned = re.sub(r"<svg\b.*?</svg>", "", fragment, flags=re.S)
    found = []
    for _tag, inner in BLOCK.findall(cleaned):
        text = visible(inner)
        if text:
            found.append(text)
    return found


def source_text(fragment: str) -> str:
    prose = visible(re.sub(r"<svg\b.*?</svg>", " ", fragment, flags=re.S))
    notes = []
    for raw in SVG_TEXT.findall(fragment):
        plain = visible(raw)
        if "PDF" in plain or "。" in plain or plain.startswith("示意"):
            notes.append(plain)
    return prose + " " + " ".join(notes)


def figure_blobs(page: str) -> list[str]:
    blobs = []
    for fig in re.findall(r"<figure\b.*?</figure>", page, flags=re.S):
        labels = " ".join(re.findall(r'aria-label="([^"]*)"', fig))
        blobs.append(visible(fig + " " + html.unescape(labels)))
    return blobs


def token_supported(token: str, source: str) -> bool:
    return re.search(rf"(?<![\d.]){re.escape(token)}(?![\d.])", source) is not None


def rel_luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    channels = [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]

    def curve(channel: float) -> float:
        if channel <= 0.04045:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (curve(channel) for channel in channels)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(foreground: str, background: str) -> float:
    lighter = max(rel_luminance(foreground), rel_luminance(background))
    darker = min(rel_luminance(foreground), rel_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


class SiteBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build.build()
        cls.public = build.PUBLIC
        cls.catalog = __import__("json").loads((ROOT / "site" / "catalog.json").read_text())

    def test_pages_exist(self):
        self.assertTrue((self.public / "index.html").is_file())
        self.assertTrue((self.public / "synthesis.html").is_file())
        self.assertEqual(len(self.catalog), 15)
        for item in self.catalog:
            page = self.public / "books" / f"{item['slug']}.html"
            self.assertTrue(page.is_file(), item["slug"])
            text = page.read_text()
            self.assertIn(item["title"], text)
            self.assertIn('role="img"', text)
            self.assertNotIn("fonts.googleapis.com", text)

    def test_disclaimer_and_footer_unchanged(self):
        for path in [self.public / "index.html", self.public / "synthesis.html"]:
            text = path.read_text()
            self.assertIn(build.DISCLAIMER, text)
            self.assertIn("本站不转载 PDF，也不做长篇原文摘录。", text)
        for item in self.catalog:
            text = (self.public / "books" / f"{item['slug']}.html").read_text()
            self.assertIn(build.DISCLAIMER, text)

    def test_prose_blocks_survive(self):
        sources = {
            self.public / "index.html": ROOT / "content" / "home.html",
            self.public / "synthesis.html": ROOT / "content" / "synthesis.html",
        }
        for item in self.catalog:
            sources[self.public / "books" / f"{item['slug']}.html"] = (
                ROOT / "content" / "books" / f"{item['slug']}.html"
            )
        for page, src in sources.items():
            output = visible(page.read_text())
            for block in blocks(src.read_text()):
                self.assertIn(block, output, f"{src.name}: {block[:80]}")

    def test_chart_source_lines_survive(self):
        for item in self.catalog:
            src = (ROOT / "content" / "books" / f"{item['slug']}.html").read_text()
            page = visible((self.public / "books" / f"{item['slug']}.html").read_text())
            for raw in SVG_TEXT.findall(src):
                plain = visible(raw)
                if "PDF" in plain or "。" in plain or plain.startswith("示意"):
                    self.assertIn(plain, page, plain)
        syn = (ROOT / "content" / "synthesis.html").read_text()
        page = visible((self.public / "synthesis.html").read_text())
        for raw in SVG_TEXT.findall(syn):
            plain = visible(raw)
            if "PDF" in plain or "。" in plain or plain.startswith("示意"):
                self.assertIn(plain, page, plain)

    def test_figure_numbers_come_from_the_essay(self):
        pages = {
            "synthesis": (
                self.public / "synthesis.html",
                ROOT / "content" / "synthesis.html",
            )
        }
        for item in self.catalog:
            pages[item["slug"]] = (
                self.public / "books" / f"{item['slug']}.html",
                ROOT / "content" / "books" / f"{item['slug']}.html",
            )
        for slug, (page_path, src_path) in pages.items():
            source = source_text(src_path.read_text())
            for blob in figure_blobs(page_path.read_text()):
                for token in TOKEN.findall(blob):
                    self.assertTrue(
                        token_supported(token, source),
                        f"{slug}: chart number {token} is not in the essay",
                    )

    def test_removed_unpublished_axis_values(self):
        synthesis = (self.public / "synthesis.html").read_text()
        for banned in ("50万", "69770", "163879", "290819", "462041", "692994"):
            self.assertNotIn(banned, synthesis)
        siegel = (self.public / "books" / "siegel.html").read_text()
        label = re.search(r'aria-label="([^"]*1802至2012[^"]*)"', siegel)
        self.assertIsNotNone(label)
        asset = html.unescape(label.group(1))
        self.assertIsNone(re.search(r"(?<![\d.])7%", asset))
        self.assertIsNone(re.search(r"(?<![\d.])3\.5%", asset))

    def test_internal_links_and_anchors(self):
        html_pages = list(self.public.rglob("*.html"))
        self.assertGreaterEqual(len(html_pages), 17)
        for page in html_pages:
            text = page.read_text()
            ids = set(re.findall(r'\sid="([^"]+)"', text))
            for href in re.findall(r'\shref="([^"]+)"', text):
                if href.startswith(("http://", "https://", "mailto:", "data:")):
                    continue
                path, _, anchor = href.partition("#")
                if path:
                    target = (page.parent / unquote(path)).resolve()
                    self.assertTrue(target.is_file(), f"{page.name} -> {href}")
                    if anchor:
                        target_ids = set(re.findall(r'\sid="([^"]+)"', target.read_text()))
                        self.assertIn(anchor, target_ids, href)
                elif anchor:
                    self.assertIn(anchor, ids, f"{page.name}#{anchor}")

    def test_no_external_images_or_pdfs(self):
        for page in self.public.rglob("*.html"):
            text = page.read_text()
            self.assertIsNone(re.search(r"<img\b[^>]*src=\"https?:", text))
            self.assertNotIn(".pdf", text.lower())
        self.assertEqual(list(ROOT.rglob("*.pdf")), [])

    def test_fonts_are_local(self):
        css = (self.public / "assets" / "style.css").read_text()
        self.assertIn("fonts/wenkai-regular.woff2", css)
        self.assertNotIn("fonts.googleapis.com", css)
        self.assertTrue((self.public / "assets" / "fonts" / "wenkai-regular.woff2").is_file())

    def test_text_contrast(self):
        pairs = [
            ("#1c1915", "#f4f1ea"),
            ("#3e4a43", "#f4f1ea"),
            ("#1a4338", "#f4f1ea"),
            ("#6e5a3a", "#f4f1ea"),
            ("#8c3a32", "#f4f1ea"),
            ("#ebe6dc", "#141816"),
            ("#c5cec8", "#141816"),
            ("#9ed0be", "#141816"),
        ]
        for foreground, background in pairs:
            self.assertGreaterEqual(contrast(foreground, background), 4.5, (foreground, background))

    def test_home_lists_every_book(self):
        home = (self.public / "index.html").read_text()
        self.assertNotIn("<!--CARDS-->", home)
        for item in self.catalog:
            self.assertIn(f"books/{item['slug']}.html", home)
            self.assertIn(item["title"], home)


if __name__ == "__main__":
    unittest.main()
