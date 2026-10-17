#!/usr/bin/env python3
"""Wrap content fragments into a static site under public/."""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

import charts

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
PUBLIC = ROOT / "public"
CSS = ROOT / "site" / "style.css"

DISCLAIMER = (
    "本站是读书笔记，只供教育与自我学习。它不是持牌金融顾问的建议，"
    "不构成对任何证券、基金或账户的推荐或招揽。投资有亏损本金的可能。"
    "新加坡 CPF、SRS、交易所产品的规则、费用与资格会变，下单前请核对官方文件。"
)

SVG_RE = re.compile(r"<svg\b([^>]*)>(.*?)</svg>", re.S)
NOTE_RE = re.compile(r"PDF|。")


def reading_minutes(body: str) -> int:
    text = re.sub(r"<[^>]+>", "", body)
    text = re.sub(r"\s+", "", text)
    # ~450 Chinese characters per minute for this register
    return max(4, round(len(text) / 450))


def svg_notes(svg: str) -> list[str]:
    notes = []
    for raw in re.findall(r"<text\b[^>]*>(.*?)</text>", svg, flags=re.S):
        plain = html.unescape(re.sub(r"<[^>]+>", "", raw))
        plain = re.sub(r"\s+", " ", plain).strip()
        if plain and (NOTE_RE.search(plain) or plain.startswith("示意")):
            notes.append(plain)
    return notes


def replace_svgs(fragment: str) -> str:
    def repl(match: re.Match) -> str:
        label_m = re.search(r'aria-label="([^"]*)"', match.group(1))
        if not label_m:
            raise SystemExit("svg missing aria-label")
        label = html.unescape(label_m.group(1))
        renderer = charts.RENDERERS.get(label)
        if renderer is None:
            raise SystemExit(f"no chart renderer for {label}")
        notes = "".join(
            f'<p class="chart-note">{html.escape(note)}</p>'
            for note in svg_notes(match.group(0))
        )
        return renderer() + notes

    return SVG_RE.sub(repl, fragment)


def insert_charts(fragment: str, slug: str) -> str:
    for anchor, snippet in charts.INSERTS.get(slug, []):
        idx = fragment.find(anchor)
        if idx < 0:
            raise SystemExit(f"{slug}: missing chart anchor {anchor}")
        end = fragment.find("</p>", idx)
        if end < 0:
            raise SystemExit(f"{slug}: anchor not inside a paragraph: {anchor}")
        end += len("</p>")
        fragment = fragment[:end] + "\n" + snippet + fragment[end:]
    return fragment


def wrap_tables(fragment: str) -> str:
    return re.sub(
        r"(<table class=\"data\">.*?</table>)",
        r'<div class="table-scroll">\1</div>',
        fragment,
        flags=re.S,
    )


def assemble(fragment: str, pager: str) -> str:
    header = ""
    head = re.search(r"<header class=\"page-head\">.*?</header>\s*", fragment, re.S)
    if head:
        header = head.group(0)
        fragment = fragment[: head.start()] + fragment[head.end() :]
    nav = ""
    nav_m = re.search(r"<nav class=\"onpage\"[^>]*>.*?</nav>\s*", fragment, re.S)
    if nav_m:
        nav = nav_m.group(0).strip()
        fragment = fragment[: nav_m.start()] + fragment[nav_m.end() :]
    if not nav and not pager:
        return header + fragment
    rail = (
        f'<aside class="rail"><p class="rail-label">本页</p>{nav}</aside>' if nav else ""
    )
    kind = "layout" if header else "layout layout-simple"
    return (
        f'<article class="reading"><div class="{kind}">{header}'
        f'<div class="reading-body">{fragment}</div>{rail}</div>'
        f"</article>{pager}"
    )


def pager_html(catalog: list[dict], index: int) -> str:
    links = []
    if index > 0:
        prev = catalog[index - 1]
        links.append(
            f'<a class="pager-prev" href="{prev["slug"]}.html">'
            f"<span>上一本</span>{html.escape(prev['title'])}</a>"
        )
    if index + 1 < len(catalog):
        nxt = catalog[index + 1]
        links.append(
            f'<a class="pager-next" href="{nxt["slug"]}.html">'
            f"<span>下一本</span>{html.escape(nxt['title'])}</a>"
        )
    else:
        links.append(
            '<a class="pager-next" href="../synthesis.html"><span>下一步</span>综合与行动</a>'
        )
    return f'<nav class="pager" aria-label="相邻书目">{"".join(links)}</nav>'


def layout(*, title: str, description: str, body: str, depth: int, current: str) -> str:
    prefix = "../" * depth
    home = f"{prefix}index.html"
    syn = f"{prefix}synthesis.html"
    css = f"{prefix}assets/style.css"
    font = f"{prefix}assets/fonts/wenkai-regular.woff2"

    def nav(href: str, label: str, key: str) -> str:
        cur = ' aria-current="page"' if current == key else ""
        return f'<a href="{href}"{cur}>{label}</a>'

    minutes = reading_minutes(body)
    body_class = {"home": "page-home", "synthesis": "page-synthesis"}.get(current, "page-book")
    icon = (
        "<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
        "viewBox='0 0 32 32'%3E%3Cpath d='M5 24c6-1 8-8 11-13 2.2-3.6 6-6.2 11-7' fill='none' "
        "stroke='%231A4338' stroke-width='2.4' stroke-linecap='round'/%3E%3C/svg%3E\">"
    )
    return f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f4f1ea" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#141816" media="(prefers-color-scheme: dark)">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
{icon}
<link rel="preload" href="{font}" as="font" type="font/woff2" crossorigin>
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
{body}
<p class="meta colophon">阅读时间约 {minutes} 分钟 · 页码指来源仓库 PDF 的文件页，含封面，不同纸书页码不会一一对应。</p>
</main>
<footer class="site">
  <div class="wrap">
    <p><strong>声明。</strong>{html.escape(DISCLAIMER)}</p>
    <p>书目来源：<a href="https://github.com/codeman008/Financial_freedom">codeman008/Financial_freedom</a>。本站不转载 PDF，也不做长篇原文摘录。</p>
  </div>
</footer>
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
    groups: dict[str, list] = {}
    for item in catalog:
        groups.setdefault(item["group"], []).append(item)
    card_html = []
    for group, items in groups.items():
        card_html.append(f'<section class="group"><h2 class="group-label">{html.escape(group)}</h2><div class="cards">')
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
        card_html.append("</div></section>")

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

    syn = insert_charts((CONTENT / "synthesis.html").read_text(), "synthesis")
    syn = replace_svgs(syn)
    syn = wrap_tables(syn)
    syn = assemble(syn, "")
    (PUBLIC / "synthesis.html").write_text(
        layout(
            title="综合原则与行动计划",
            description="十五本书的共同原则、分歧，以及面向新加坡读者的分步行动计划。",
            body=syn,
            depth=0,
            current="synthesis",
        )
    )

    for index, item in enumerate(catalog):
        fragment = (CONTENT / "books" / f"{item['slug']}.html").read_text()
        fragment = insert_charts(fragment, item["slug"])
        fragment = replace_svgs(fragment)
        fragment = wrap_tables(fragment)
        fragment = assemble(fragment, pager_html(catalog, index))
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


if __name__ == "__main__":
    build()
