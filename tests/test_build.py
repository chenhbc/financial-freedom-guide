"""Build checks for the published report page."""
from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]

APPENDIX = (
    "下面三地只用官方页面能确认的工具，说明前面的步骤可以落在哪里。"
    "结构相同：有哪些账户，对应哪几步，要避开什么。不写利率、顶额和提取年龄；"
    "这些以当时的官方页面为准。这不是对任何账户或产品的推荐。"
)
SANS = (
    '-apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", '
    '"Microsoft YaHei", "Noto Sans SC", sans-serif'
)


def _load_build():
    spec = importlib.util.spec_from_file_location("site_build", ROOT / "site" / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.check_call([sys.executable, "site/build.py"], cwd=ROOT)
        cls.build = _load_build()
        cls.public = ROOT / "public"
        cls.html = (cls.public / "index.html").read_text()
        cls.css = (cls.public / "assets" / "site.css").read_text()

    def test_no_google_fonts(self):
        for path in self.public.rglob("*"):
            if path.suffix not in {".html", ".css", ".js", ".json", ".txt"}:
                continue
            text = path.read_text(errors="ignore")
            self.assertNotIn("fonts.googleapis.com", text, path)
            self.assertNotIn("fonts.gstatic.com", text, path)
            self.assertNotIn("fonts.google.com", text, path)
        self.assertNotIn("Source Han Sans", self.css)

    def test_single_stylesheet(self):
        links = []
        for line in self.html.splitlines():
            if "rel=\"stylesheet\"" in line or "rel='stylesheet'" in line:
                links.append(line.strip())
        self.assertEqual(links, ['<link rel="stylesheet" href="assets/site.css">'])
        self.assertFalse((self.public / "assets" / "style.css").exists())
        self.assertFalse((self.public / "assets" / "report.css").exists())
        self.assertFalse((ROOT / "site" / "style.css").exists())
        self.assertFalse((ROOT / "site" / "report.css").exists())

    def test_onpage_hidden_below_1200(self):
        self.assertIn("@media (max-width: 1199px)", self.css)
        self.assertRegex(
            self.css,
            r"@media \(max-width: 1199px\) \{\s*\.onpage \{ display: none; \}\s*\}",
        )
        self.assertIn("@media (min-width: 1200px)", self.css)
        self.assertIn("position: fixed", self.css)

    def test_no_footer_curve_or_animation(self):
        self.assertNotIn("footer-mark", self.html)
        self.assertNotIn("<svg", self.html)
        for token in ("draw-curve", "curve-rise", "margin-curve", "curve-mark", "@keyframes"):
            self.assertNotIn(token, self.css)

    def test_appendix_intro_is_meta_and_text_is_unchanged(self):
        self.assertIn(f'<p class="meta">{APPENDIX}</p>', self.html)
        self.assertNotIn('class="lede"', self.html)
        self.assertNotIn(".lede {", self.css)
        self.assertNotIn(".lede{", self.css)
        self.assertIn(".lede-note", self.css)

    def test_system_font_stack_keeps_tabular_nums(self):
        self.assertIn(f"--sans: {SANS};", self.css)
        self.assertIn("font-variant-numeric: tabular-nums lining-nums;", self.css)
        self.assertIn("font-variant-numeric: tabular-nums;", self.css)
        self.assertIn("font-size: 17px;", self.css)
        self.assertIn("line-height: 1.8;", self.css)
        self.assertIn("font-weight: 400;", self.css)

    def test_wenkai_is_self_hosted_swap_with_license(self):
        self.assertGreaterEqual(self.css.count("font-display: swap"), 2)
        self.assertIn('url("fonts/wenkai-regular.woff2")', self.css)
        self.assertIn('url("fonts/wenkai-medium.woff2")', self.css)
        ofl = (self.public / "assets" / "fonts" / "OFL.txt").read_text()
        self.assertIn("SIL OPEN FONT LICENSE", ofl)
        self.assertEqual(
            (ROOT / "site" / "fonts" / "OFL.txt").read_bytes(),
            (self.public / "assets" / "fonts" / "OFL.txt").read_bytes(),
        )

    def test_subset_covers_kai_characters_only(self):
        chars = self.build.kai_characters(self.html)
        self.assertEqual(len(chars[400]), 39)
        self.assertEqual(len(chars[700]), 43)
        for weight, name in ((400, "wenkai-regular.woff2"), (700, "wenkai-medium.woff2")):
            path = self.public / "assets" / "fonts" / name
            self.assertEqual(path.read_bytes()[:4], b"wOF2")
            font = TTFont(path)
            cmap = set()
            for table in font["cmap"].tables:
                if table.isUnicode():
                    cmap.update(table.cmap)
            missing = [ch for ch in chars[weight] if ord(ch) not in cmap]
            self.assertEqual(missing, [], name)
            versions = [
                rec.toUnicode()
                for rec in font["name"].names
                if rec.nameID == 5
            ]
            self.assertTrue(any("1.522" in version for version in versions), versions)
        # A body-only character must not be required. Whole-page subsetting
        # would pull it in; the kai subset does not.
        self.assertNotIn("新", chars[400] + chars[700])
        regular = self.public / "assets" / "fonts" / "wenkai-regular.woff2"
        medium = self.public / "assets" / "fonts" / "wenkai-medium.woff2"
        total = regular.stat().st_size + medium.stat().st_size
        self.assertLess(regular.stat().st_size, 191520)
        self.assertLess(medium.stat().st_size, 190356)
        self.assertLess(total, 48_000)
        self.assertGreater(total, 8_000)
        for weight, sentinel in ((400, "投资者"), (400, "睡觉"), (700, "页注"), (700, "最终")):
            self.assertTrue(all(ch in chars[weight] for ch in sentinel), sentinel)

    def test_subset_is_deterministic(self):
        page = self.build.layout((ROOT / "content" / "report.html").read_text())
        first = Path(tempfile.mkdtemp())
        second = Path(tempfile.mkdtemp())
        try:
            self.build.subset_wenkai(page, first)
            self.build.subset_wenkai(page, second)
            for name in ("wenkai-regular.woff2", "wenkai-medium.woff2"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes(), name)
        finally:
            shutil.rmtree(first)
            shutil.rmtree(second)

    def test_source_font_pin_unchanged(self):
        for meta in self.build.WENKAI_SOURCES.values():
            path = ROOT / "site" / "fonts" / meta["file"]
            digest = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, meta["sha256"])
        self.assertEqual(self.build.WENKAI_VERSION, "1.522")

    def test_disclaimer_and_colophon_text(self):
        self.assertIn(self.build.DISCLAIMER, self.html)
        self.assertIn(
            "本站不转载 PDF，也不做长篇原文摘录。",
            self.html,
        )
        self.assertIn(
            '<p class="meta colophon">页码为来源 PDF 的文件页（含封面），<span class="nw">与纸书页码不一一对应。</span></p>',
            self.html,
        )
        self.assertNotIn("阅读时间约", self.html)
        self.assertIn("全文约 18 分钟。", self.html)

    def test_alpha_text(self):
        self.assertIn(
            "核心提取标到原书章节，历史数字标到 PDF 页码 · 不推荐任何产品",
            re.sub(r"<[^>]+>", "", self.html),
        )
        self.assertNotIn("最终财富自由 · 报告", self.html)
        self.assertIn('<h2 id="action">二、原则与做法</h2>', self.html)
        self.assertIn('<h3 id="findings">原则</h3>', self.html)
        self.assertIn('<a href="#findings">原则</a>', self.html)
        self.assertIn('<h2 id="gist">先看结论</h2>', self.html)
        self.assertNotIn("先记住这一句", self.html)
        self.assertNotIn("要拿走的一句", self.html)
        self.assertNotIn('class="remember"', self.html)
        self.assertNotIn('class="callout"', self.html)
        self.assertNotIn("<h3>注意</h3>", self.html)
        self.assertIn('<p class="meta">这里不排阅读顺序，也不把两本书写成对错。</p>', self.html)
        self.assertNotIn("每条只留一个想法", self.html)
        self.assertNotIn("下列书名只为对照页注", self.html)
        self.assertIn("金额空着。完成前面的步骤之前，不要跳到后面更像投资的动作。", self.html)
        self.assertIn("下表是美国一段很长历史的描述，不是预测，也不是你所在市场的预期。", self.html)
        self.assertIn("<p>别处写下的估值分界不能换一个交易所继续用。</p>", self.html)
        self.assertIn(
            "<p>书中 2017 年前后的盈利收益率分界，绑的是当时的债券基金平均收益和当时的国债收益率，不能当作今天的阈值。"
            '<sup class="fn"><a href="#n6">6</a></sup></p>',
            self.html,
        )
        self.assertIn("<p>强积金里的基金选择不是对某只港交所基金的推荐。</p>", self.html)
        self.assertIn("<h4>账户与工具</h4>", self.html)
        self.assertIn("<h4>对应到通用步骤</h4>", self.html)
        self.assertNotIn("规则、费用和资格会变。", self.html)
        self.assertNotIn("不在这里写缴费比例", self.html)
        self.assertNotIn("不在这里写供款比率", self.html)

    def test_mobile_wrap_markup(self):
        text = re.sub(r"<[^>]+>", "", self.html)
        self.assertIn('<span class="seg">· 不推荐任何产品</span>', self.html)
        self.assertIn("核心提取标到原书章节，历史数字标到 PDF 页码 · 不推荐任何产品", text)
        self.assertIn('<span class="nw">敌人</span>', self.html)
        self.assertIn("「投资者的最大问题甚至是最可怕的敌人，很可能就是他们自己。」", text)
        self.assertIn(
            '<cite>—— <span class="nw">格雷厄姆《聪明的投资者》导言「本书的目的」，</span><span class="nw">PDF 第 26 页</span></cite>',
            self.html,
        )
        self.assertIn("—— 格雷厄姆《聪明的投资者》导言「本书的目的」，PDF 第 26 页", text)
        self.assertIn("页码为来源 PDF 的文件页（含封面），与纸书页码不一一对应。", text)
        self.assertIn(".quote .nw", self.css)
        self.assertIn(".colophon .nw", self.css)
        self.assertNotIn("text-indent", self.css)
        self.assertNotIn("hanging-punctuation", self.css)
        self.assertIn(".quote cite, .epigraph cite { display: block;", self.css)

    def test_dead_selectors_are_gone(self):
        for token in (
            ".cards",
            ".card ",
            ".chips",
            ".statrow",
            ".hero-aside",
            ".notice",
            ".prose",
            ".figure",
            ".group-label",
            ".page-head",
            "ol.conclusions",
            ".two {",
            ".toc a",
            ".toc {",
            ".toc li",
        ):
            self.assertNotIn(token, self.css, token)
        for token in (".toc-group", ".toc-sub", ".onpage", ".extract", ".checklist"):
            self.assertIn(token, self.css, token)
        self.assertNotIn(".remember", self.css)
        self.assertNotIn(".callout", self.css)

    def test_no_pdf_added(self):
        pdfs = [path for path in ROOT.rglob("*.pdf") if ".git" not in path.parts]
        self.assertEqual(pdfs, [])


if __name__ == "__main__":
    unittest.main()
