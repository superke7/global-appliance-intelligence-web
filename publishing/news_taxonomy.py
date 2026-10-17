#!/usr/bin/env python3
"""Public news-tag vocabulary; keeps source text independent from browsing facets."""
from __future__ import annotations

import json
import re
from pathlib import Path

TAXONOMY = json.loads((Path(__file__).resolve().parents[1] / "config/news-taxonomy.json").read_text(encoding="utf-8"))
GEO_HIERARCHY = json.loads((Path(__file__).resolve().parents[1] / "config/news-geo-hierarchy.json").read_text(encoding="utf-8"))

STAGE_PATTERNS = [
    ("诉讼裁决", r"法院|裁决|诉讼|起诉|上诉|司法|违宪|法官|判决"),
    ("调查审查", r"调查|审查|听证|核查|核验|评估|咨询|问询|执法调查|反倾销"),
    ("暂停延期", r"暂停|延期|暂缓|冻结|推迟|暂定|中止|搁置"),
    ("结束撤销", r"撤销|取消|终止|停止|关闭|落幕|结束"),
    ("谈判磋商", r"磋商|谈判|协商|洽谈|谈判进展|协议文本定稿|对话|协调"),
    ("规划拟议", r"拟议|拟推|提案|草案|立法|征求意见|政策评估|政策预告|预研"),
    ("已生效/投产", r"已生效|生效执行|已实施|落地执行|正式实施|已经实施|已投产|正式投产|投产运行|建成投运|已签署|正式签署|已完成|收购完成|并购完成|开始执行|实施中"),
    ("已宣布待实施", r"已公告|已宣布|已公布|将于|待生效|待启动|尚未实施|计划启动|即将|公告发布|获批|协议签署待"),
    ("数据/结果发布", r"发布|报告|公布数据|业绩|月度数据|调查结果|销量|增长|预测|统计"),
    ("推进中", r"推进|进行|持续|建设|扩张|推广|部署|优化|启动|讨论|准备|落地|测试|试点|合作|阶段|新品|上线|市场|运营|整合|复苏|开发|调整|执行|投资|发展"),
]


def stage_tag(raw: str) -> str | None:
    raw = str(raw or "").strip()
    if raw in TAXONOMY["stage_overrides"]:
        return TAXONOMY["stage_overrides"][raw]
    # A definite first-stage action takes precedence over later negotiation notes.
    if re.match(r"^(已生效|已实施|已投产|正式投产|投产运行|已经实施)", raw):
        return "已生效/投产"
    if re.match(r"^(已公告|已宣布|已公布)", raw):
        return "已宣布待实施"
    for name, pattern in STAGE_PATTERNS:
        if re.search(pattern, raw):
            return name
    return None


def news_mark_tag(raw: str) -> str | None:
    s = str(raw or "")
    if "历史迁移" in s:
        return "历史收录"
    if any(v in s for v in ("补录", "补漏", "旧闻")):
        return "历史补录"
    if "新事件" in s:
        return "新事件"
    if any(v in s for v in ("既有事件", "新增进展", "阶段切换")):
        return "事件进展"
    if any(v in s for v in ("今日新增", "竞品动态", "市场动态", "战略观察", "市场数据", "政策信号", "核心供应链")):
        return "独立资讯"
    return None


def impact_tag(raw: str) -> str | None:
    m = re.match(r"^(中高|高|中|低)(?![高低])", str(raw or "").strip())
    return m.group(1) if m else None


def category_tag(raw: str) -> str | None:
    s = str(raw or "").strip()
    head = re.split(r"[/／]", s)[0].strip()
    if head in TAXONOMY["facets"]["category"]:
        return head
    if re.search(r"^(贸易政策|Section 338|关税|产业政策|贸易谈判|区域贸易协定|原产地|制裁|反制关税|232关税|反转运|双边贸易|政策司法|关税诉讼|钢铁配额|双边贸易协定|强迫劳动|碳关税|贸易救济|CBAM|原产地规则|进口税|保障措施)", head) or re.search(r"关税|进出口限制|贸易协定|反倾销|反补贴|反转运|外国补贴|301|232|338|贸易保护|原产地", s):
        return "贸易与政策"
    if re.search(r"^(监管与供应链|能效标准|生态设计|网络安全|安全监管|海关监管)", head) or re.search(r"监管|网络安全|强制认证|合规|标准|安全漏洞|回收", s):
        return "监管与供应链"
    if re.search(r"^(投资与合作|并购|合资|股权投资|收购|资本|融资)", head) or re.search(r"并购|合资|股权|资本运作|股权投资|基金", s):
        return "投资与合作"
    if re.search(r"^(制造与产能|新产线|新建工厂|制造布局|裁员|产能调整)", head) or re.search(r"工厂|产能|产线|制造|生产基地|本地化生产|零部件本地化", s):
        return "制造与产能"
    if re.search(r"^(市场与渠道|竞品动态|市场需求|市场|市场进入|渠道能力建设|产品规模|品牌授权|经营业绩|重组|渠道扩张|产品|品牌|消费)", head) or re.search(r"市场|渠道|销量|产品|出口数据|需求|业绩|营收|订单|客户", s):
        return "市场与渠道"
    return None


def geo_tags(raw: str) -> list[str]:
    out = []
    names = set(TAXONOMY["geo_canonical"])
    aliases = TAXONOMY["geo_aliases"]
    for chunk in re.split(r"[/／、；;，,]|(?:及其他)|(?:以及)", str(raw or "")):
        part = chunk.strip()
        part = re.sub(r"^(?:重点|包括|特别是|主要涉及)", "", part).strip()
        canonical = aliases.get(part, part)
        if canonical in names and canonical not in out:
            out.append(canonical)
    return out



def expand_geo_filter_tags(geographies: list[str]) -> list[str]:
    """Geographic *coverage* filters, not news actors/policy jurisdictions.

    One-directional: France -> EU/Europe, but Europe does not imply EU.
    Preserve explicit Sheet labels; derive additional matches at render time.
    Member relationships are a versioned October 2026 snapshot.
    """
    if not isinstance(geographies, list) or any(not isinstance(x, str) for x in geographies):
        raise TypeError("Expected the already-normalized explicit geographic labels")

    memberships = GEO_HIERARCHY["organization_membership"]
    regions = GEO_HIERARCHY["country_region_membership"]
    parents = GEO_HIERARCHY["region_parents"]
    result: list[str] = []
    visited: set[str] = set()

    def add(value: str) -> None:
        if value and value not in visited:
            visited.add(value)
            result.append(value)

    for place in geographies:
        add(place)
        for region in regions.get(place, []):
            add(region)
        for organization, members in memberships.items():
            if place in members:
                add(organization)

    # Resolve region parents transitively and only upwards.
    index = 0
    while index < len(result):
        for parent in parents.get(result[index], []):
            add(parent)
        index += 1
    return result


def normalize_labels(row: dict) -> dict:
    """Input contains only five approved, public Sheet label fields."""
    required = ("事件阶段", "国家/地区", "新闻标注", "影响程度", "事件分类")
    if set(row) != set(required):
        raise ValueError("only five expressly approved Sheet fields are allowed")
    raw = {k: str(row[k] or "").strip() for k in required}
    tags = {
        "stage": stage_tag(raw["事件阶段"]),
        "geographies": geo_tags(raw["国家/地区"]),
        "news_mark": news_mark_tag(raw["新闻标注"]),
        "impact": impact_tag(raw["影响程度"]),
        "category": category_tag(raw["事件分类"]),
    }
    missing = [k for k in ("stage", "news_mark", "impact", "category") if not tags[k]]
    if missing:
        raise ValueError("unresolved tags must be reviewed: " + ",".join(missing))
    for key, choices in (("stage","stage"), ("news_mark","news_mark"), ("impact","impact"), ("category","category")):
        if tags[key] not in TAXONOMY["facets"][choices]:
            raise ValueError("unknown standard tag")
    return {"raw": raw, "tags": tags}
