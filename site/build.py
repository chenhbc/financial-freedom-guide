#!/usr/bin/env python3
"""Wrap content fragments into a static site under public/."""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
PUBLIC = ROOT / "public"
CSS = ROOT / "site" / "style.css"

DISCLAIMER = (
    "本报告根据公开书籍整理，只供教育与自我学习。它不是持牌金融顾问的建议，"
    "不构成对任何证券、基金或账户的推荐或招揽。投资有亏损本金的可能。"
    "新加坡、中国内地与香港的账户规则、费用与资格会变，下单前请核对官方文件。"
)


def reading_minutes(body: str) -> int:
    text = re.sub(r"<[^>]+>", "", body)
    text = re.sub(r"\s+", "", text)
    # ~450 Chinese characters per minute for this register
    return max(4, round(len(text) / 450))


def layout(*, title: str, description: str, body: str, depth: int, current: str) -> str:
    prefix = "../" * depth
    home = f"{prefix}index.html"
    syn = f"{prefix}synthesis.html"
    css = f"{prefix}assets/style.css"

    def nav(href: str, label: str, key: str) -> str:
        cur = ' aria-current="page"' if current == key else ""
        return f'<a href="{href}"{cur}>{label}</a>'

    minutes = reading_minutes(body)
    body_class = {"home": "page-home", "synthesis": "page-synthesis"}.get(current, "page-book")
    return f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600&display=swap">
<link rel="stylesheet" href="{css}">
</head>
<body class="{body_class}">
<a class="skip" href="#main">跳到正文</a>
<header class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="{home}">十五本书的投资笔记</a>
    <nav class="nav" aria-label="主导航">
      {nav(home, "书目", "home")}
      {nav(syn, "综合与行动", "synthesis")}
    </nav>
  </div>
</header>
<main id="main" class="wrap">
<div class="margin-curve" aria-hidden="true">
  <svg class="curve-mark" viewBox="0 0 72 20" width="72" height="20" fill="none">
    <line x1="1" y1="17.5" x2="70" y2="17.5" stroke="#C5D4CE" stroke-width="1"/>
    <path d="M2 16.2 C 16 16.2, 30 16, 43 14.6 C 52 12.4, 60 7.2, 70 2.2" stroke="#1B463C" stroke-width="1.5" stroke-linecap="round" fill="none"/>
  </svg>
</div>
{body}
<p class="meta colophon">阅读时间约 {minutes} 分钟 · 页码指来源仓库 PDF 的文件页，含封面，不同纸书页码不会一一对应。</p>
</main>
<footer class="site">
  <div class="wrap">
    <p><strong>声明。</strong>{html.escape(DISCLAIMER)}</p>
    <p>书目来源：<a href="https://github.com/codeman008/Financial_freedom">codeman008/Financial_freedom</a>。本站不转载 PDF，也不做长篇原文摘录。</p>
  </div>
</footer>
<script>
(function () {{
  var links = Array.prototype.slice.call(document.querySelectorAll(".onpage a"));
  if (!links.length) return;
  var items = links.map(function (a) {{
    var id = a.getAttribute("href");
    return {{ a: a, el: id ? document.querySelector(id) : null }};
  }}).filter(function (item) {{ return item.el; }});
  if (!items.length) return;
  function update() {{
    var y = window.scrollY + 96;
    var current = items[0];
    items.forEach(function (item) {{
      if (item.el.offsetTop <= y) current = item;
    }});
    items.forEach(function (item) {{
      if (item === current) item.a.setAttribute("aria-current", "true");
      else item.a.removeAttribute("aria-current");
    }});
  }}
  update();
  window.addEventListener("scroll", update, {{ passive: true }});
}})();
</script>
</body>
</html>
"""


def build() -> None:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    (PUBLIC / "assets").mkdir(parents=True)
    (PUBLIC / "books").mkdir()
    shutil.copy(CSS, PUBLIC / "assets" / "style.css")
    font_src = ROOT / "site" / "fonts"
    font_dst = PUBLIC / "assets" / "fonts"
    font_dst.mkdir(parents=True)
    for font in font_src.iterdir():
        if font.suffix in {".woff2", ".txt"}:
            shutil.copy(font, font_dst / font.name)

    catalog = json.loads((ROOT / "site" / "catalog.json").read_text())
    home_extra = (CONTENT / "home.html").read_text()
    cards = []
    groups: dict[str, list] = {}
    for item in catalog:
        groups.setdefault(item["group"], []).append(item)
    card_html = []
    for group, items in groups.items():
        card_html.append(f'<h2 class="group-label">{html.escape(group)}</h2><div class="cards">')
        for item in items:
            body = (CONTENT / "books" / f"{item['slug']}.html").read_text()
            minutes = reading_minutes(body)
            card_html.append(
                f"""<a class="card" href="books/{item['slug']}.html">
  <div class="idx">{html.escape(item['index'])}</div>
  <div class="card-body">
    <h3>{html.escape(item['title'])}</h3>
    <p>{html.escape(item['blurb'])}</p>
    <p class="foot"><span>{html.escape(item['author'])}</span><span>约 {minutes} 分钟</span></p>
  </div>
</a>"""
            )
        card_html.append("</div>")

    home_body = home_extra.replace("<!--CARDS-->", "\n".join(card_html))
    (PUBLIC / "index.html").write_text(
        layout(
            title="十五本书的投资笔记",
            description="根据公开书库中的原书文本整理的投资与个人理财读书笔记。",
            body=home_body,
            depth=0,
            current="home",
        )
    )

    syn = (CONTENT / "synthesis.html").read_text()
    (PUBLIC / "synthesis.html").write_text(
        layout(
            title="综合原则与行动计划",
            description="十五本书的共同原则、分歧，以及面向新加坡读者的分步行动计划。",
            body=syn,
            depth=0,
            current="synthesis",
        )
    )

    for item in catalog:
        fragment = (CONTENT / "books" / f"{item['slug']}.html").read_text()
        (PUBLIC / "books" / f"{item['slug']}.html").write_text(
            layout(
                title=f"{item['title']} · 读书笔记",
                description=item["blurb"],
                body=fragment,
                depth=1,
                current="",
            )
        )
    print(f"built {len(catalog)} books -> {PUBLIC}")
    write_report()


REPORT_TOC_SCRIPT = """<script>
(function () {
  var groups = Array.prototype.slice.call(document.querySelectorAll(".toc-group"));
  var items = [];
  groups.forEach(function (group) {
    Array.prototype.forEach.call(group.querySelectorAll("a"), function (a) {
      var id = a.getAttribute("href");
      var el = id ? document.querySelector(id) : null;
      if (el) items.push({ a: a, el: el, group: group });
    });
  });
  if (!items.length) return;
  function update() {
    var y = window.scrollY + 96;
    var current = items[0];
    items.forEach(function (item) {
      var top = item.el.getBoundingClientRect().top + window.scrollY;
      if (top <= y) current = item;
    });
    items.forEach(function (item) {
      if (item === current) item.a.setAttribute("aria-current", "true");
      else item.a.removeAttribute("aria-current");
    });
    groups.forEach(function (group) {
      if (group === current.group) group.classList.add("is-open");
      else group.classList.remove("is-open");
    });
  }
  update();
  window.addEventListener("scroll", update, { passive: true });
})();
</script>"""


def write_report() -> None:
    """Add the standalone report without replacing the book pages."""
    shutil.copy(ROOT / "site" / "report.css", PUBLIC / "assets" / "report.css")
    body = (CONTENT / "report.html").read_text()
    page = layout(
        title="最终财富自由",
        description="一份可以单独阅读的财富自由报告：先给结论，再写出来源和做法。不是投资建议。",
        body=body,
        depth=0,
        current="report",
    )
    page = page.replace(
        '<link rel="stylesheet" href="assets/style.css">',
        '<link rel="stylesheet" href="assets/style.css">\n'
        '<link rel="stylesheet" href="assets/report.css">',
        1,
    )
    page = page.replace(
        f"{html.escape(DISCLAIMER)}</p>",
        f"{html.escape(DISCLAIMER)} 附录中的内地与香港工具同样只以当时的官方页面为准。</p>",
        1,
    )
    page = re.sub(r"<script>.*?</script>", REPORT_TOC_SCRIPT, page, count=1, flags=re.S)
    (PUBLIC / "report.html").write_text(page)


if __name__ == "__main__":
    build()
