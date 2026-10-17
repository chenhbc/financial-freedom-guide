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
    "本站是读书笔记，只供教育与自我学习。它不是持牌金融顾问的建议，"
    "不构成对任何证券、基金或账户的推荐或招揽。投资有亏损本金的可能。"
    "新加坡 CPF、SRS、交易所产品的规则、费用与资格会变，下单前请核对官方文件。"
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
    return f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="stylesheet" href="{css}">
</head>
<body>
<a class="skip" href="#main">跳到正文</a>
<header class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="{home}">十五本书的投资笔记<small>FINANCIAL FREEDOM NOTES</small></a>
    <nav class="nav" aria-label="主导航">
      {nav(home, "书目", "home")}
      {nav(syn, "综合与行动", "synthesis")}
    </nav>
  </div>
</header>
<main id="main" class="wrap">
{body}
<p class="meta" style="margin-top:28px">阅读时间约 {minutes} 分钟 · 页码指来源仓库 PDF 的文件页，含封面，不同纸书页码不会一一对应。</p>
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
  <h3>{html.escape(item['title'])}</h3>
  <p>{html.escape(item['blurb'])}</p>
  <div class="foot">{html.escape(item['author'])} · 约 {minutes} 分钟</div>
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


if __name__ == "__main__":
    build()
