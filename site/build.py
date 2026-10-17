#!/usr/bin/env python3
"""Build the report site into public/. The homepage is the report."""
from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
PUBLIC = ROOT / "public"
CSS = ROOT / "site" / "style.css"
REPORT_CSS = ROOT / "site" / "report.css"

DISCLAIMER = (
    "本报告根据公开书籍整理，只供教育与自我学习。它不是持牌金融顾问的建议，"
    "不构成对任何证券、基金或账户的推荐或招揽。投资有亏损本金的可能。"
    "新加坡、中国内地与香港的账户规则、费用与资格会变，下单前请核对官方文件。"
    "附录中的内地与香港工具同样只以当时的官方页面为准。"
)


def reading_minutes(body: str) -> int:
    text = re.sub(r"<[^>]+>", "", body)
    text = re.sub(r"\s+", "", text)
    return max(4, round(len(text) / 450))


def layout(body: str) -> str:
    minutes = reading_minutes(body)
    return f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>财富自由，第一步不是买股票｜最终财富自由</title>
<meta name="description" content="一份可以单独阅读的财富自由报告：先给结论，再写出来源和做法。不是投资建议。">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600&display=swap">
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/report.css">
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
<p class="meta colophon">阅读时间约 {minutes} 分钟 · 页码指来源仓库 PDF 的文件页，含封面，不同纸书页码不会一一对应。</p>
</main>
<footer class="site">
  <div class="wrap">
    <p class="footer-mark" aria-hidden="true">
      <svg viewBox="0 0 72 20" width="72" height="20" fill="none">
        <line x1="1" y1="17.5" x2="70" y2="17.5" stroke="#C5D4CE" stroke-width="1"/>
        <path d="M2 16.2 C 16 16.2, 30 16, 43 14.6 C 52 12.4, 60 7.2, 70 2.2" stroke="#C5D4CE" stroke-width="1.5" stroke-linecap="round" fill="none"/>
      </svg>
    </p>
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


def build() -> None:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    (PUBLIC / "assets" / "fonts").mkdir(parents=True)
    shutil.copy(CSS, PUBLIC / "assets" / "style.css")
    shutil.copy(REPORT_CSS, PUBLIC / "assets" / "report.css")
    font_src = ROOT / "site" / "fonts"
    for font in font_src.iterdir():
        if font.suffix in {".woff2", ".txt"}:
            shutil.copy(font, PUBLIC / "assets" / "fonts" / font.name)
    body = (CONTENT / "report.html").read_text()
    (PUBLIC / "index.html").write_text(layout(body))
    (PUBLIC / "report.html").write_text(redirect("index.html"))
    print(f"built report -> {PUBLIC}")


if __name__ == "__main__":
    build()
