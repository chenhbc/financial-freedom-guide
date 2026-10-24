#!/usr/bin/env python3
"""Build the report site into public/. The homepage is the report.

LXGW WenKai is subset at build time to the characters the page actually
draws in that face. See site/fonts/SOURCE.md.
"""
from __future__ import annotations

import hashlib
import html
import shutil
from html.parser import HTMLParser
from pathlib import Path

try:
    from fontTools.subset import Options, Subsetter
    from fontTools.ttLib import TTFont
except ImportError as exc:  # pragma: no cover - exercised only without the dep
    raise SystemExit(
        "fontTools is required to subset LXGW WenKai. "
        "Install it with: python3 -m pip install -r requirements.txt"
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
PUBLIC = ROOT / "public"
CSS = ROOT / "site" / "site.css"
FONT_DIR = ROOT / "site" / "fonts"

# Pinned LXGW WenKai v1.522 (17 March 2026).
# https://github.com/lxgw/LxgwWenKai/releases/tag/v1.522
WENKAI_VERSION = "1.522"
WENKAI_SOURCES = {
    400: {
        "file": "wenkai-regular.woff2",
        "sha256": "fb87ae45b0543bf877f01409dfee757339d83ea9420eabf0323e6cdab5aa7352",
    },
    700: {
        "file": "wenkai-medium.woff2",
        "sha256": "29ef82ff317fa12c0b80f94fbbecdd1cd48a952ed2ed4efdeae9f1d2ca16f758",
    },
}

DISCLAIMER = (
    "本报告根据公开书籍整理，只供教育与自我学习。它不是持牌金融顾问的建议，"
    "不构成对任何证券、基金或账户的推荐或招揽。投资有亏损本金的可能。"
    "新加坡、中国内地与香港的账户规则、费用与资格会变，下单前请核对官方文件。"
    "附录中的内地与香港工具同样只以当时的官方页面为准。"
)

_VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "source",
    "track",
    "wbr",
}
_SKIP_TEXT = {"script", "style", "noscript"}


class _El:
    def __init__(self, tag: str, classes: set[str], parent: _El | None) -> None:
        self.tag = tag
        self.classes = classes
        self.parent = parent
        self.children: list[_El | str] = []


class _DomParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _El("#document", set(), None)
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes: set[str] = set()
        for key, value in attrs:
            if key == "class" and value:
                classes = set(value.split())
        el = _El(tag, classes, self.stack[-1])
        self.stack[-1].children.append(el)
        if tag not in _VOID:
            self.stack.append(el)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in _VOID and self.stack[-1].tag == tag:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def _has_ancestor(el: _El, class_name: str) -> bool:
    node = el.parent
    while node is not None:
        if class_name in node.classes:
            return True
        node = node.parent
    return False


def _font_spec(el: _El) -> tuple[str, int] | None:
    """Font set directly on this element.

    WenKai is used for the brand, headings, and the hero and epigraph
    quotations. Citations stay on the sans stack. Weight 700 is the Medium
    file; weight 400 is Regular.
    """
    if el.tag == "cite":
        return ("sans", 400)
    if el.tag in {"h1", "h2"} or "brand" in el.classes:
        return ("kai", 700)
    if el.tag == "p" and _has_ancestor(el, "quote"):
        return ("kai", 400)
    if el.tag == "p" and _has_ancestor(el, "epigraph"):
        return ("kai", 400)
    if el.tag == "blockquote" and "quote" in el.classes:
        return ("kai", 400)
    return None


def _keep_char(ch: str) -> bool:
    return ch not in "\n\r\t\f\v "


def kai_characters(document: str) -> dict[int, str]:
    """Characters drawn in LXGW WenKai, keyed by CSS font-weight (400 or 700)."""
    parser = _DomParser()
    parser.feed(document)
    buckets: dict[int, list[str]] = {400: [], 700: []}

    def walk(el: _El, inherited: tuple[str, int]) -> None:
        if el.tag in _SKIP_TEXT:
            return
        spec = _font_spec(el)
        family, weight = spec if spec is not None else inherited
        for child in el.children:
            if isinstance(child, str):
                if family == "kai":
                    buckets[weight].append(child)
            else:
                walk(child, (family, weight))

    walk(parser.root, ("sans", 400))
    return {weight: _unique(chunks) for weight, chunks in buckets.items()}


def _unique(chunks: list[str]) -> str:
    seen: set[str] = set()
    chars: list[str] = []
    for chunk in chunks:
        for ch in chunk:
            if not _keep_char(ch) or ch in seen:
                continue
            seen.add(ch)
            chars.append(ch)
    chars.sort()
    return "".join(chars)


def layout(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>财富自由，第一步不是买股票｜最终财富自由</title>
<meta name="description" content="一份可以单独阅读的财富自由报告：先给结论，再写出来源和做法。不是投资建议。">
<link rel="stylesheet" href="assets/site.css">
</head>
<body class="page-home">
<a class="skip" href="#main">跳到正文</a>
<header class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="index.html">最终财富自由</a>
    <nav class="nav" aria-label="本页">
      <a href="#gist" data-nav="gist">结论</a>
      <a href="#extract" data-nav="extract">核心</a>
      <a href="#action" data-nav="action">做法</a>
      <a href="#places" data-nav="places">例子</a>
      <a href="#sources" data-nav="sources">书目</a>
    </nav>
  </div>
</header>
<main id="main" class="wrap">
{body}
<p class="meta colophon">页码为来源 PDF 的文件页（含封面），与纸书页码不一一对应。</p>
</main>
<footer class="site">
  <div class="wrap">
    <p><strong>声明。</strong>{html.escape(DISCLAIMER)}</p>
    <p>材料来源：<a href="https://github.com/codeman008/Financial_freedom">codeman008/Financial_freedom</a>。本站不转载 PDF，也不做长篇原文摘录。</p>
  </div>
</footer>
<script>
(function () {{
  var groups = Array.prototype.slice.call(document.querySelectorAll(".toc-group"));
  var navLinks = Array.prototype.slice.call(document.querySelectorAll(".nav a"));
  var items = [];
  groups.forEach(function (group) {{
    Array.prototype.forEach.call(group.querySelectorAll("a"), function (a) {{
      var id = a.getAttribute("href");
      var el = id ? document.querySelector(id) : null;
      if (el) items.push({{ a: a, el: el, group: group }});
    }});
  }});
  if (!items.length) return;
  function update() {{
    var y = window.scrollY + 96;
    var current = items[0];
    items.forEach(function (item) {{
      var top = item.el.getBoundingClientRect().top + window.scrollY;
      if (top <= y) current = item;
    }});
    items.forEach(function (item) {{
      if (item === current) item.a.setAttribute("aria-current", "true");
      else item.a.removeAttribute("aria-current");
    }});
    var key = current.group.getAttribute("data-nav");
    groups.forEach(function (group) {{
      if (group === current.group) group.classList.add("is-open");
      else group.classList.remove("is-open");
    }});
    navLinks.forEach(function (a) {{
      if (a.getAttribute("data-nav") === key) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    }});
  }}
  update();
  window.addEventListener("scroll", update, {{ passive: true }});
}})();
</script>
</body>
</html>
"""


def redirect(target: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{target}">
<title>最终财富自由</title>
<script>location.replace({target!r});</script>
</head>
<body>
<p><a href="{target}">最终财富自由</a></p>
</body>
</html>
"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _assert_source_font(path: Path, sha256: str) -> None:
    actual = _sha256(path)
    if actual != sha256:
        raise SystemExit(
            f"{path} sha256 {actual} does not match the pinned LXGW WenKai "
            f"{WENKAI_VERSION} file {sha256}. See site/fonts/SOURCE.md."
        )
    font = TTFont(path)
    versions = []
    for record in font["name"].names:
        if record.nameID == 5:
            versions.append(record.toUnicode())
    if not any(WENKAI_VERSION in version for version in versions):
        raise SystemExit(
            f"{path.name} is not LXGW WenKai {WENKAI_VERSION} "
            f"(name table: {versions}). See site/fonts/SOURCE.md."
        )


def _unicode_cmap(font: TTFont) -> set[int]:
    codes: set[int] = set()
    for table in font["cmap"].tables:
        if table.isUnicode():
            codes.update(table.cmap)
    return codes


def _subset_font(src: Path, dest: Path, text: str) -> None:
    missing = [ch for ch in text if ord(ch) not in _unicode_cmap(TTFont(src))]
    if missing:
        raise SystemExit(
            f"{src.name} has no glyph for: {''.join(missing)}. "
            "The pinned WenKai source does not cover this page."
        )
    font = TTFont(src)
    options = Options()
    options.flavor = "woff2"
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.name_languages = ["*"]
    options.notdef_glyph = True
    options.notdef_outline = True
    options.recommended_glyphs = True
    subsetter = Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    font.flavor = "woff2"
    # The source timestamp is part of the pinned font. Do not stamp "now",
    # or every build would emit a different woff2.
    font.recalcTimestamp = False
    font.save(dest)


def subset_wenkai(document: str, dest_dir: Path) -> dict[int, Path]:
    """Write one woff2 per kai weight, covering only characters used at that weight."""
    chars = kai_characters(document)
    dest_dir.mkdir(parents=True, exist_ok=True)
    written: dict[int, Path] = {}
    total = 0
    for weight, meta in WENKAI_SOURCES.items():
        src = FONT_DIR / meta["file"]
        _assert_source_font(src, meta["sha256"])
        dest = dest_dir / meta["file"]
        text = chars.get(weight, "")
        _subset_font(src, dest, text)
        size = dest.stat().st_size
        total += size
        written[weight] = dest
        print(
            f"subset {meta['file']}: {len(text)} chars, {size} bytes "
            f"(source {src.stat().st_size} bytes)"
        )
    print(f"subset total: {total} bytes")
    return written


def build() -> None:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    (PUBLIC / "assets" / "fonts").mkdir(parents=True)
    shutil.copy(CSS, PUBLIC / "assets" / "site.css")
    shutil.copy(FONT_DIR / "OFL.txt", PUBLIC / "assets" / "fonts" / "OFL.txt")
    body = (CONTENT / "report.html").read_text()
    page = layout(body)
    subset_wenkai(page, PUBLIC / "assets" / "fonts")
    (PUBLIC / "index.html").write_text(page)
    (PUBLIC / "report.html").write_text(redirect("index.html"))
    print(f"built report -> {PUBLIC}")


if __name__ == "__main__":
    build()
