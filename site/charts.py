"""Figures for the reading site.

Data charts use only numbers printed in the essay. Bar lengths are a scale,
not new observations. Diagrams that are not measurements say 示意.
"""
from __future__ import annotations

import html
import math


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def plate(aria: str, body: str) -> str:
    return (
        f'<div class="plate" role="img" aria-label="{esc(aria)}">{body}</div>'
    )


def figure(aria: str, body: str, caption: str) -> str:
    return (
        '<figure class="figure">'
        f"{plate(aria, body)}"
        f"<figcaption>{esc(caption)}</figcaption>"
        "</figure>"
    )


def _cols(items: list[dict]) -> str:
    cells = []
    for item in items:
        tone = item.get("tone", "")
        cells.append(
            "<div class=\"col\">"
            "<span class=\"col-plot\">"
            f"<span class=\"col-bar {tone}\" style=\"height:{item['ratio']:.4f}%\"></span>"
            "</span>"
            f"<span class=\"col-val\">{esc(item['value'])}</span>"
            f"<span class=\"col-name\">{esc(item['name'])}</span>"
            "</div>"
        )
    return f'<div class="cols">{"".join(cells)}</div>'


def _hbars(items: list[dict]) -> str:
    rows = []
    for item in items:
        tone = item.get("tone", "")
        left = item.get("left", 0.0)
        rows.append(
            "<div class=\"hbar\">"
            f"<span class=\"hbar-name\">{esc(item['name'])}</span>"
            "<span class=\"hbar-track\" aria-hidden=\"true\">"
            f"<span class=\"hbar-fill {tone}\" "
            f"style=\"left:{left:.4f}%;width:{item['ratio']:.4f}%\"></span>"
            "</span>"
            f"<span class=\"hbar-num\">{esc(item['value'])}</span>"
            "</div>"
        )
    return f'<div class="hbars">{"".join(rows)}</div>'


def _triad(items: list[tuple[str, list[str]]], emph: int | None = None) -> str:
    cells = []
    for i, (title, lines) in enumerate(items):
        klass = " class=\"is-emph\"" if emph == i else ""
        spans = "".join(f"<span>{esc(line)}</span>" for line in lines)
        cells.append(f"<li{klass}><b>{esc(title)}</b>{spans}</li>")
    return f'<ul class="triad">{"".join(cells)}</ul>'


def _rules(items: list[tuple[str, str, str]]) -> str:
    rows = []
    for name, detail, tone in items:
        rows.append(
            "<li>"
            f"<i class=\"swatch {tone}\" aria-hidden=\"true\"></i>"
            f"<b>{esc(name)}</b>"
            f"<span>{esc(detail)}</span>"
            "</li>"
        )
    return f'<ul class="rules">{"".join(rows)}</ul>'


def compound() -> str:
    # Endpoints printed in the synthesis essay. Heights share one scale.
    terminal = {
        "投入": 360_000,
        "4%": 694_049,
        "6%": 1_004_515,
        "8%": 1_490_359,
    }
    top = terminal["8%"]
    items = [
        {"name": "投入", "value": "360,000 元", "ratio": 100 * terminal["投入"] / top, "tone": "soft"},
        {"name": "4% 终值", "value": "694,049 元", "ratio": 100 * terminal["4%"] / top, "tone": "mid"},
        {"name": "6% 终值", "value": "1,004,515 元", "ratio": 100 * terminal["6%"] / top, "tone": ""},
        {"name": "8% 终值", "value": "1,490,359 元", "ratio": 100.0, "tone": "mid"},
    ]
    aria = (
        "示意演算，不是预测。每月投入 1,000 新加坡元，30 年、360 期。"
        "本金 360,000 元。年化 4% 终值约 694,049 元，6% 终值约 1,004,515 元，"
        "8% 终值约 1,490,359 元。柱高按这些金额的比例，从零起算。"
    )
    return plate(aria, _cols(items))


def siegel_assets() -> str:
    values = [("股票", "6.6%", 6.6, ""), ("长期国债", "3.6%", 3.6, "mid"),
              ("短期债券", "2.7%", 2.7, "soft"), ("黄金", "0.7%", 0.7, "brass")]
    top = 6.6
    items = [
        {"name": name, "value": label, "ratio": 100 * raw / top, "tone": tone}
        for name, label, raw, tone in values
    ]
    aria = (
        "1802至2012年实际年复合收益柱状图。股票 6.6%，长期国债 3.6%，"
        "短期债券 2.7%，黄金 0.7%。柱高按这些百分比从零起算。"
        "短期债券的 2.7% 按原句，没有再写一次真实。"
    )
    return plate(aria, _cols(items))


def siegel_periods() -> str:
    rows = [("1802–1870 年", "6.7%", 6.7), ("1871–1925 年", "6.6%", 6.6),
            ("1926–2012 年", "6.4%", 6.4)]
    top = 6.7
    items = [
        {"name": name, "value": label, "ratio": 100 * raw / top}
        for name, label, raw in rows
    ]
    return figure(
        "1802–1870 年 6.7%，1871–1925 年 6.6%，1926–2012 年 6.4%。柱长从零起算，所以三段差不多高。",
        _hbars(items),
        "三段都是股票实际收益，见上一段。柱长按百分比从零起算。PDF 第 181 页。",
    )


def index_terminal() -> str:
    # Log10 from the stated 1 dollar, so 704,997 and 4.52 can share a row.
    points = [
        ("股票", "704,997 美元", 704_997, ""),
        ("债券", "1,778 美元", 1_778, "mid"),
        ("短期债券", "281 美元", 281, "soft"),
        ("黄金", "4.52 美元", 4.52, "brass"),
    ]
    top = math.log10(704_997)
    items = []
    for name, label, raw, tone in points:
        items.append({
            "name": name,
            "value": label,
            "ratio": 100 * math.log10(raw) / top,
            "tone": tone,
        })
    return figure(
        "1802–2002 年，1 美元变成股票 704,997 美元、债券 1,778 美元、短期债券 281 美元、黄金 4.52 美元。柱长按终端金额的常用对数，从 1 美元算起。",
        _hbars(items),
        "终端财富，不是年化。柱长按常用对数，便于和 4.52 美元放在一起；请读数字。见 PDF 第 26 页，第 51 页记在《股市长线法宝》名下，窗口仍到 2002 年。",
    )


def index_domestic() -> str:
    points = [("股票基金", "6,215 元", 6215, ""), ("债券基金", "2,273 元", 2273, "mid"),
              ("货币基金", "1,435 元", 1435, "soft")]
    top = 6215
    items = [
        {"name": name, "value": label, "ratio": 100 * raw / top, "tone": tone}
        for name, label, raw, tone in points
    ]
    return figure(
        "2003 年年底到 2017 年 5 月底，1,000 元放到股票基金变成 6,215 元，债券基金 2,273 元，货币基金 1,435 元。",
        _hbars(items),
        "书中给出的终端金额，不是年化。柱长按终端金额从零起算。起点都是 1,000 元。见 PDF 第 51–52 页。",
    )


def index_fees() -> str:
    # Full scale is the stated top of the active-fund range, 2%.
    items = [
        {"name": "国内指数管理费", "value": "0.6%", "ratio": 100 * 0.6 / 2},
        {"name": "国内指数托管费", "value": "0.1%", "ratio": 100 * 0.1 / 2, "tone": "mid"},
        {"name": "主动基金常见管理费", "value": "1%–2%", "left": 50.0, "ratio": 50.0, "tone": "soft"},
        {"name": "美股主流指数", "value": "0.2% 以下", "ratio": 100 * 0.2 / 2, "tone": "mid"},
        {"name": "有的指数基金", "value": "0.05%", "ratio": 100 * 0.05 / 2, "tone": "soft"},
        {"name": "SPY", "value": "0.09%", "ratio": 100 * 0.09 / 2, "tone": "soft"},
    ]
    return figure(
        "写作时的费率印象：国内指数管理费 0.6%、托管费 0.1%；主动基金常见管理费 1%–2%；美股主流指数 0.2% 以下，有的 0.05%；SPY 0.09%。",
        _hbars(items),
        "这些费率会过时。1%–2% 画成区间，0.2% 以下画到 0.2%。满刻度是书里写出的 2%。见 PDF 第 48 页。",
    )


def index_yield_example() -> str:
    body = (
        '<ul class="eq">'
        "<li><span>盈利</span><b>1 亿元</b></li>"
        "<li><span>市值</span><b>8 亿元</b></li>"
        "<li><span>市盈率</span><b>8 倍</b></li>"
        "<li><span>盈利收益率</span><b>12.5%</b></li>"
        "</ul>"
    )
    return figure(
        "书中例子：盈利 1 亿元、市值 8 亿元，市盈率 8 倍，盈利收益率 12.5%。",
        body,
        "盈利收益率定义为 E/P，约等于市盈率的倒数。见 PDF 第 165 页。",
    )


def index_japan() -> str:
    items = [
        {"name": "1990 年", "value": "6.0%", "ratio": 100.0},
        {"name": "1992 年", "value": "1.1%", "ratio": 100 * 1.1 / 6.0, "tone": "risk"},
    ]
    body = '<p class="call-num"><span>1989 年市盈率</span><b>70.6 倍</b></p>' + _hbars(items)
    return figure(
        "1989 年市盈率 70.6 倍。经济增长率从 1990 年的 6.0% 降到 1992 年的 1.1%。柱长只比较这两年的增长率。",
        body,
        "市盈率和增长率不是同一刻度。见 PDF 第 334–335 页。",
    )


def index_bands() -> str:
    body = _rules([
        ("盈利收益率 > 10%", "坚持定投", ""),
        ("6.4% 到 10%", "暂停定投，继续持有", "soft"),
        ("低于 6.4%", "分批卖出", "risk"),
    ])
    return plate(
        "盈利收益率三段：大于 10% 坚持定投，6.4% 到 10% 暂停定投并继续持有，低于 6.4% 分批卖出。三档不是一条连续刻度。",
        body,
    )


def graham_mr_market() -> str:
    return plate(
        "示意。市场先生每天报价，情绪会过度。企业报表是你自己的估价依据。",
        _triad([
            ("市场先生", ["每天报价，情绪会过度"]),
            ("企业报表", ["你自己的估价依据"]),
        ]),
    )


def graham_yields() -> str:
    points = [
        ("1949 年债券", "2.66%", 2.66, "soft"),
        ("1949 年股息", "6.82%", 6.82, ""),
        ("1972 年债券", "7.19%", 7.19, "mid"),
        ("1972 年股息", "2.76%", 2.76, "soft"),
    ]
    top = 7.19
    items = [
        {"name": name, "value": label, "ratio": 100 * raw / top, "tone": tone}
        for name, label, raw, tone in points
    ]
    return figure(
        "1949 年债券收益率 2.66%、工业股股息 6.82%。1972 年最高等级债券利息 7.19%、工业股股息 2.76%。",
        _hbars(items),
        "导言里的美国市场切片，来自穆迪 AAA 级债券和工业股。不是今天的收益率。见 PDF 第 23 页。",
    )


def graham_band() -> str:
    body = (
        '<div class="band">'
        '<div class="band-track" aria-hidden="true">'
        '<span class="band-fill" style="left:25%;width:50%"></span>'
        "</div>"
        '<div class="band-scale" aria-hidden="true">'
        '<span class="band-tick" style="left:25%">25%</span>'
        '<span class="band-tick" style="left:75%">75%</span>'
        "</div>"
        "<p class=\"band-caption\">股票不低于资金的 25%，不高于 75%；债券则在 75% 与 25% 之间对应。</p>"
        "</div>"
    )
    return figure(
        "示意防御型股票仓带宽：不低于 25%，不高于 75%。债券在 75% 与 25% 之间对应。不是一份建议持仓。",
        body,
        "示意 PDF 第 76 页的区间，不是新加坡 CPF 的比例，也不是永远的 50/50。",
    )


def allocation_pyramid() -> str:
    body = (
        '<div class="pyramid">'
        '<div class="py" style="width:68%"><i class="" aria-hidden="true"></i><span>近期必须支出 · 现金类</span></div>'
        '<div class="py" style="width:84%"><i class="mid" aria-hidden="true"></i><span>保值与名义稳定 · 债券等</span></div>'
        '<div class="py" style="width:100%"><i class="soft" aria-hidden="true"></i><span>成长 · 股票等长期购买力</span></div>'
        "</div>"
    )
    return plate(
        "示意配置层次，没有百分比：近期必须支出用现金类，保值与名义稳定用债券等，成长用股票等长期购买力。",
        body,
    )


def allocation_studies() -> str:
    items = [
        {"name": "82 家，1977–1987", "value": "91.5%", "ratio": 91.5},
        {"name": "97 种大型养老基金", "value": "87%", "ratio": 87.0, "tone": "mid"},
    ]
    return figure(
        "两项研究：82 家养老基金在 1977–1987 年的样本里，投资收益差异的 91.5% 来自资产配置；97 种大型养老基金的差异中 87% 与资产类别选择有关。",
        _hbars(items),
        "柱长按正文的百分比。两项样本不同，不能相加，也不是“能赚到市场的 91.5%”。见 PDF 第 5 页。",
    )


def statements() -> str:
    return plate(
        "示意三张报表：资产负债表是照相机，利润表是摄像机，现金流量表记录经营、投资、融资。不是书中的原图。",
        _triad([
            ("资产负债表", ["照相机 · 某一天", "有什么、欠什么"]),
            ("利润表", ["摄像机 · 一段时期", "赚没赚、如何确认"]),
            ("现金流量表", ["现金从哪进、到哪去", "经营 / 投资 / 融资"]),
        ]),
    )


def crowd() -> str:
    return plate(
        "示意群体的三个原因：数量与匿名使责任感消失，传染使感情和行动传开，暗示类似催眠、人格退后。",
        _triad([
            ("数量与匿名", ["责任感消失"]),
            ("传染", ["感情和行动会传开"]),
            ("暗示", ["类似催眠，人格退后"]),
        ], emph=2),
    )


def levers() -> str:
    return plate(
        "示意三类杠杆。劳动力和资本需要许可。代码与媒体的复制边际成本为零，不需要许可。",
        _triad([
            ("劳动力", ["别人替你工作", "需要许可"]),
            ("资本", ["别人的钱", "需要许可"]),
            ("代码与媒体", ["复制边际成本为零", "不需要许可"]),
        ], emph=2),
    )


def goose() -> str:
    return plate(
        "示意。鹅是不再花掉的本金，金蛋是可以讨论怎么用的利息，愿望罐要写明用途。故事里的一半是角色的选择。",
        _triad([
            ("鹅 · 本金", ["不再花掉"]),
            ("金蛋 · 利息", ["可以讨论怎么用"]),
            ("愿望罐", ["写明用途"]),
        ]),
    )


def three_questions() -> str:
    return plate(
        "示意三个问题：估值最好学，品质真正拉开差距，时机作者自认最弱。不是书中的原图。",
        _triad([
            ("估值", ["最好学"]),
            ("品质", ["真正拉开差距"]),
            ("时机", ["作者自认最弱"]),
        ], emph=1),
    )


def qiu_framework() -> str:
    body = (
        '<p class="stack-label">四种周期 · 示意</p>'
        '<ol class="seq"><li>政策周期</li><li>市场（估值）周期</li><li>经济周期</li><li>盈利周期</li></ol>'
        '<p class="stack-label">三种杠杆 · 示意</p>'
        '<ol class="seq"><li>财务杠杆 · 对利率的弹性</li>'
        "<li>运营杠杆 · 对经济的弹性</li>"
        "<li>估值杠杆 · 对剩余流动性的弹性</li></ol>"
    )
    return figure(
        "示意。四种周期：政策周期、市场（估值）周期、经济周期、盈利周期。三种杠杆：财务杠杆、运营杠杆、估值杠杆。不是书中的原图。",
        body,
        "名称见 PDF 第 125–126 页。排列是笔记的，不是书里的原图，也不表示见底次序。",
    )


def fisher_growth() -> str:
    items = [
        {"name": "长期每年成长", "value": "12%", "ratio": 100 * 12 / 20, "tone": "mid"},
        {"name": "长期每年成长", "value": "20%", "ratio": 100.0},
    ]
    return figure(
        "示意对照，不是预测：长期每年成长 12% 与 20%。",
        _hbars(items),
        "用来说明第三种换股理由。这是说明，不是预测。",
    )


def cashflow() -> str:
    body = (
        '<div class="ledger">'
        '<div class="ledger-from">收入</div>'
        '<div class="ledger-to">'
        "<div><b>资产</b><span>现金流入口袋</span><em>再投入</em></div>"
        '<div class="is-risk"><b>负债</b><span>现金流出口袋</span></div>'
        "</div></div>"
    )
    return plate(
        "示意，不是会计恒等式。收入可以流向资产并再投入，资产把现金流放入口袋；负债把现金流从口袋取走。",
        body,
    )


def two_prices() -> str:
    return plate(
        "示意。价格相对价值足够低，详尽分析后可称为投资操作。价格成为唯一尺度时，同一种证券变成投机。",
        _triad([
            ("价格相对价值足够低", ["详尽分析后，可称为投资操作"]),
            ("价格成为唯一尺度", ["同一种证券变成投机"]),
        ]),
    )


def pendulum() -> str:
    svg = (
        '<svg class="spark" viewBox="0 0 640 88" aria-hidden="true">'
        '<line x1="48" y1="28" x2="592" y2="28" stroke="currentColor" stroke-width="1.5"/>'
        '<path d="M320 28 Q 470 78 592 28" fill="none" stroke="currentColor" stroke-width="1.5"/>'
        '<circle cx="48" cy="28" r="5" fill="currentColor"/>'
        '<circle cx="320" cy="28" r="5" fill="currentColor"/>'
        '<circle cx="592" cy="28" r="5" fill="currentColor"/>'
        "</svg>"
    )
    labels = _triad([
        ("恐惧 / 过低价格", []),
        ("中点", []),
        ("贪婪 / 过高价格", []),
    ])
    return plate(
        "示意市场心理钟摆：恐惧与过低价格、中点、贪婪与过高价格。不是价格序列。",
        svg + labels,
    )


def munger_circle() -> str:
    body = (
        '<div class="ability">'
        "<b>能力圈</b>"
        "<span>只在自己明确界定的能力圈内行事</span>"
        "<span>没有边界的能力根本不能称之为能力。</span>"
        "</div>"
    )
    return figure(
        "示意。只在自己明确界定的能力圈内行事。没有边界的能力根本不能称之为能力。",
        body,
        "示意，不是书中的原图。见 PDF 第 38 页与第 71 页。",
    )


def resistance() -> str:
    svg = (
        '<svg class="spark" viewBox="0 0 640 96" aria-hidden="true">'
        '<path d="M12 74 C 90 74, 130 24, 210 36 S 330 80, 430 42 S 560 20, 628 30" '
        'fill="none" stroke="currentColor" stroke-width="2"/>'
        '<circle cx="300" cy="58" r="4.5" fill="currentColor"/>'
        "</svg>"
        '<p class="spark-label">不猜最高点</p>'
    )
    return plate(
        "示意最小阻力路线，不是书中的价格序列。标记的意思是不猜最高点。",
        svg,
    )


RENDERERS = {
    "每月1000元、年化6%的示意终值": compound,
    "1802至2012年实际年复合收益柱状图": siegel_assets,
    "配置层次": allocation_pyramid,
    "三张报表与三类活动": statements,
    "群体的三个原因": crowd,
    "盈利收益率三段": index_bands,
    "市场先生与企业价值": graham_mr_market,
    "最小阻力路线示意": resistance,
    "市场心理钟摆": pendulum,
    "三类杠杆": levers,
    "本金与利息分开": goose,
    "估值品质时机": three_questions,
    "收入如何流向资产或负债": cashflow,
    "价格决定投资还是投机": two_prices,
}


INSERTS: dict[str, list[tuple[str, str]]] = {
    "siegel": [
        ("1926–2012 年 6.4%", siegel_periods()),
    ],
    "indexfund": [
        ("704,997", index_terminal()),
        ("6,215", index_domestic()),
        ("0.09%", index_fees()),
        ("12.5%", index_yield_example()),
        ("70.6", index_japan()),
    ],
    "graham": [
        ("7.19%", graham_yields() + graham_band()),
    ],
    "allocation": [
        ("91.5%", allocation_studies()),
    ],
    "fisher": [
        ("12% 与 20%", fisher_growth()),
    ],
    "qiu": [
        ("在烟花声中卖出", qiu_framework()),
    ],
    "munger": [
        ("没有边界的能力不能称为能力", munger_circle()),
    ],
}
