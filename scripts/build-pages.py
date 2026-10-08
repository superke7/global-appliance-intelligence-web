#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = ROOT / "public-batches"
OUT = ROOT / "_site"
SITE_TITLE = "全球家电AI早报"
SITE_DESCRIPTION = "全球家电、贸易政策、供应链与制造布局公开资讯"
SITE_URL = "https://superke7.github.io/global-appliance-intelligence-web/"
RSS_MAX_ITEMS = 300
BJT = timezone(timedelta(hours=8))
RSS_AUTHOR = SITE_TITLE

STYLE = """
:root{color-scheme:light;--bg:#f6f7f9;--card:#fff;--text:#18202a;--muted:#667085;--line:#e5e7eb;--accent:#075c66;--accent2:#0f62fe;--soft:#f3f5f8;--max:1180px;--shadow:0 16px 40px rgba(16,24,40,.07)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text)}a{color:inherit;text-decoration:none}.wrap{max-width:var(--max);margin:auto;padding:0 20px}
.top{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:24px;padding-top:14px;padding-bottom:14px}.brand{font-weight:800;font-size:18px;color:var(--accent)}.nav{display:flex;gap:20px;font-size:15px;color:#344054}.nav a:hover,.text-link:hover,.item-title:hover{color:var(--accent)}
.hero{padding:30px 0 22px}.hero-dashboard{display:flex;justify-content:space-between;align-items:flex-start;gap:28px}.hero-main{min-width:0}.hero h1{font-size:34px;margin:0 0 8px;letter-spacing:-.02em}.sub{color:var(--muted);line-height:1.7}.stats-box{min-width:355px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:15px 18px;box-shadow:0 8px 24px rgba(16,24,40,.04)}.stats-label{font-size:13px;color:var(--muted);margin-bottom:9px}.stats-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.stat-item{border-left:1px solid var(--line);padding-left:12px}.stat-item:first-child{border-left:0;padding-left:0}.stat{font-size:24px;font-weight:800;line-height:1.05}.stat-name{font-size:12px;color:var(--muted);margin-top:5px}
.home-grid{display:grid;grid-template-columns:245px minmax(0,1fr);gap:24px;align-items:start}.archive-side{position:sticky;top:76px}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;margin-bottom:16px}.archive-panel{padding:16px}.archive-panel h3{margin:0 0 12px;font-size:17px}.archive-panel .all-link{display:block;margin-top:12px;font-size:13px;color:var(--accent2)}
.month{border-top:1px solid var(--line)}.month:first-of-type{border-top:0}.month summary{cursor:pointer;list-style:none;padding:12px 2px;font-weight:700;font-size:14px}.month summary::-webkit-details-marker{display:none}.month summary::after{content:"＋";float:right;color:var(--muted)}.month[open] summary::after{content:"－"}.day-list{list-style:none;padding:0 0 8px;margin:0}.day-list li{margin:1px 0}.day-list a{display:flex;justify-content:space-between;gap:8px;padding:8px 9px;border-radius:8px;font-size:13px;color:#344054}.day-list a:hover{background:var(--soft);color:var(--accent)}.day-count{color:var(--muted);white-space:nowrap}.sidebar-events{padding:16px}.sidebar-events h3{margin:0 0 10px;font-size:17px}.sidebar-event-list{list-style:none;padding:0;margin:0;max-height:540px;overflow:auto}.sidebar-event-list li{border-top:1px solid var(--line)}.sidebar-event-list li:first-child{border-top:0}.sidebar-event-list a{display:block;padding:10px 2px}.sidebar-event-list a:hover .sidebar-event-title{color:var(--accent)}.sidebar-event-title{font-size:13px;line-height:1.45;font-weight:700;color:#344054}.sidebar-event-date{font-size:12px;color:var(--muted);margin-top:4px}.sidebar-events .all-link{display:block;margin-top:12px;font-size:13px;color:var(--accent2)}
.section-title{margin:0 0 14px;font-size:22px}.news{transition:box-shadow .15s ease,border-color .15s ease}.news:hover{border-color:#cfd5dd;box-shadow:0 8px 22px rgba(16,24,40,.05)}.news h2{font-size:21px;line-height:1.45;margin:0 0 10px}.item-title{font-weight:750;color:#075c66;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px}.meta{font-size:13px;color:var(--muted);margin-bottom:10px}.excerpt{line-height:1.78;color:#344054}.source,.text-link{font-size:13px;color:var(--accent2)}.item-actions{display:flex;gap:16px;flex-wrap:wrap;margin-top:14px}.event-link{font-size:13px;color:var(--accent);font-weight:650}.pill{display:inline-block;padding:4px 9px;border:1px solid var(--line);border-radius:999px;font-size:12px;color:#475467;margin:3px 4px 3px 0;background:#fff}
.archive-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}.archive-grid .card{margin:0}.event-list{display:grid;gap:14px}.event-card-link{display:block}.event{margin:0;transition:transform .15s ease,box-shadow .15s ease,border-color .15s ease}.event-card-link:hover .event{transform:translateY(-1px);border-color:#cfd5dd;box-shadow:0 8px 22px rgba(16,24,40,.06)}.event h2{font-size:19px;margin:0 0 10px}.event .progress{line-height:1.75;color:#344054}
.detail-shell{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:30px;margin-top:22px;box-shadow:var(--shadow)}.detail-title{font-size:32px;line-height:1.35;margin:0 0 22px}.detail-meta{display:flex;gap:12px 24px;flex-wrap:wrap;padding:14px 0 18px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);color:var(--muted);font-size:14px}.detail-content{font-size:16px;line-height:1.9;padding:22px 0}.detail-content p{margin:0 0 16px}.detail-content ul,.detail-content ol{padding-left:24px}.detail-content a{color:var(--accent2);text-decoration:underline}.source-list{list-style:none;padding:0;margin:8px 0 0}.source-list li{padding:6px 0}.source-list a{color:var(--accent2);text-decoration:underline;text-underline-offset:2px}.detail-event{background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:18px;margin-top:10px}.detail-event h3{margin:0 0 9px}.backline{margin:22px 0 0;font-size:14px;color:var(--accent2)}
.info-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px 16px}.info-box{background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:16px}.info-label{font-size:13px;color:var(--muted);font-weight:700;margin-bottom:8px}.info-value{line-height:1.7}.detail-section{border-top:1px solid var(--line);padding-top:20px;margin-top:20px}.detail-section h2{font-size:20px;margin:0 0 14px}.related-list{list-style:none;padding:0;margin:0}.related-item{padding:16px 0;border-bottom:1px solid var(--line)}.related-item:last-child{border-bottom:0}.related-date{font-size:13px;color:var(--muted);margin-bottom:8px}.related-title{font-weight:750;line-height:1.55;color:var(--accent)}.related-excerpt{color:#344054;line-height:1.7;margin-top:8px}
.footer{color:var(--muted);font-size:13px;padding:34px 0 48px}.empty{padding:40px 0;color:var(--muted)}
@media(max-width:900px){.hero-dashboard{flex-direction:column}.stats-box{min-width:0;width:100%}.home-grid{grid-template-columns:1fr}.archive-side{position:static}.archive-panel{padding:14px}.info-grid{grid-template-columns:1fr}}
@media(max-width:650px){.nav{gap:12px;font-size:13px;flex-wrap:wrap;justify-content:flex-end}.top .wrap{align-items:flex-start}.hero h1,.detail-title{font-size:27px}.detail-shell{padding:20px}.stats-row{gap:8px}.stat{font-size:21px}}
"""


def load_batches():
    batches = []
    if not BATCH_ROOT.exists():
        return batches
    for path in sorted(BATCH_ROOT.glob("*/public-batch.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        date_key = path.parent.name
        if len(date_key) == 8 and date_key.isdigit():
            batches.append((date_key, data))
    return batches


def fmt_day(key: str) -> str:
    try:
        return datetime.strptime(key, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return key


def fmt_day_cn(key: str) -> str:
    try:
        dt = datetime.strptime(key, "%Y%m%d")
        return f"{dt.month}月{dt.day:02d}日"
    except ValueError:
        return key


def fmt_month_cn(key: str) -> str:
    try:
        dt = datetime.strptime(key + "01", "%Y%m%d")
        return f"{dt.year}年{dt.month}月"
    except ValueError:
        return key


def safe_text(value) -> str:
    return html.escape(str(value or ""))


def fmt_public_date_cn(value) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw[:8] if fmt == "%Y%m%d" else raw[:10], fmt)
            return f"{dt.year}年{dt.month}月{dt.day}日"
        except ValueError:
            pass
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return f"{dt.year}年{dt.month}月{dt.day}日"
    except ValueError:
        return raw


def safe_component(value, fallback="item") -> str:
    value = str(value or "").strip().lower()
    cleaned = re.sub(r"[^a-z0-9._-]+", "-", value).strip("-._")
    return cleaned or fallback


def safe_external_url(value) -> str:
    raw = str(value or "").strip()
    try:
        parsed = urlparse(raw)
    except ValueError:
        return ""
    return raw if parsed.scheme in {"http", "https"} and parsed.netloc else ""


class PublicHTMLSanitizer(HTMLParser):
    allowed_tags = {"p", "br", "strong", "b", "em", "i", "ul", "ol", "li", "blockquote", "a"}
    void_tags = {"br"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.allowed_tags:
            return
        if tag == "a":
            href = ""
            for key, value in attrs:
                if key == "href":
                    href = safe_external_url(value)
                    break
            if href:
                self.out.append(f'<a href="{html.escape(href, quote=True)}" target="_blank" rel="noopener noreferrer">')
            else:
                self.out.append("<a>")
        elif tag in self.void_tags:
            self.out.append(f"<{tag}>")
        else:
            self.out.append(f"<{tag}>")

    def handle_endtag(self, tag):
        if tag in self.allowed_tags and tag not in self.void_tags:
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        self.out.append(html.escape(data))

    def get_html(self):
        return "".join(self.out)


def strip_supplemental_source_blocks(value) -> str:
    raw = str(value or "")
    if not raw:
        return ""
    # “补充来源”中的链接会继续由下方“原始来源”统一展示，正文不重复显示。
    # 兼容 <p>、<div>、<li> 等常见块级标签，以及标签内含链接/强调标签的情况。
    patterns = [
        r"<p\\b[^>]*>\\s*(?:<[^>]+>\\s*)*补充来源\\s*[：:]?.*?</p>",
        r"<div\\b[^>]*>\\s*(?:<[^>]+>\\s*)*补充来源\\s*[：:]?.*?</div>",
        r"<li\\b[^>]*>\\s*(?:<[^>]+>\\s*)*补充来源\\s*[：:]?.*?</li>",
    ]
    for pattern in patterns:
        raw = re.sub(pattern, "", raw, flags=re.IGNORECASE | re.DOTALL)
    return raw


def sanitize_content_html(value) -> str:
    if not value:
        return ""
    parser = PublicHTMLSanitizer()
    parser.feed(strip_supplemental_source_blocks(value))
    parser.close()
    return parser.get_html()


class SourceLinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current_href = ""
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        self.current_href = ""
        self.current_text = []
        for key, value in attrs:
            if key == "href":
                self.current_href = safe_external_url(value)
                break

    def handle_data(self, data):
        if self.current_href:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current_href:
            label = "".join(self.current_text).strip()
            self.links.append((self.current_href, label))
            self.current_href = ""
            self.current_text = []


def extract_original_sources(item: dict):
    sources = []
    seen = set()
    primary_url = safe_external_url(item.get("source_url"))
    if primary_url:
        sources.append((primary_url, str(item.get("source_name") or "").strip() or urlparse(primary_url).netloc))
        seen.add(primary_url)

    content_html = str(item.get("content_html") or "")
    if content_html:
        parser = SourceLinkExtractor()
        parser.feed(content_html)
        parser.close()
        for url, label in parser.links:
            if not url or url in seen:
                continue
            sources.append((url, label or urlparse(url).netloc))
            seen.add(url)
    return sources


def parse_bjt_timestamp(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def batch_publish_time(date_key: str, batch: dict):
    target = parse_bjt_timestamp(batch.get("target_publish_at_bjt"))
    if target and target.strftime("%Y%m%d") == date_key:
        return target
    try:
        day = datetime.strptime(date_key, "%Y%m%d")
    except ValueError:
        return None
    # Historical fallback only; normal public batches carry target_publish_at_bjt.
    return day.replace(hour=7, minute=50, second=0, microsecond=0, tzinfo=BJT)


def cdata(value) -> str:
    return "<![CDATA[" + str(value or "").replace("]]>", "]]]]><![CDATA[>") + "]]>"


def rss_source_html(item: dict):
    source_date = html.escape(str(item.get("source_published_date") or ""))
    sources = extract_original_sources(item)
    details = []
    if sources:
        source_links = "；".join(
            f'<a href="{html.escape(url, quote=True)}" rel="noopener noreferrer external">{html.escape(label)}</a>'
            for url, label in sources
        )
        details.append(f"<strong>来源：</strong>{source_links}")
    elif item.get("source_name"):
        details.append(f"<strong>来源：</strong>{html.escape(str(item.get('source_name')))}")
    if source_date:
        details.append(f"<strong>来源日期：</strong>{source_date}")
    return "｜".join(details)


def rss_description_html(item: dict):
    excerpt = html.escape(str(item.get("excerpt") or ""))
    source_line = rss_source_html(item)
    return f"<p>{excerpt}</p>" + (f'<p class="gai-feed-source">{source_line}</p>' if source_line else "")


def rss_content_html(item: dict):
    content = sanitize_content_html(item.get("content_html"))
    if not content:
        content = f'<p>{html.escape(str(item.get("excerpt") or ""))}</p>'
    source_line = rss_source_html(item)
    if source_line and 'class="gai-feed-source"' not in content:
        content = content.rstrip() + "\n" + f'<p class="gai-feed-source">{source_line}</p>'
    return content


def rss_pubdate(value):
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=BJT)
    return format_datetime(value.astimezone(timezone.utc))


def article_slug(item: dict, date_key: str, index: int) -> str:
    fallback = f"gai-{date_key}-{index + 1:03d}"
    return safe_component(item.get("public_id"), fallback)


def event_slug(event: dict) -> str:
    return safe_component(event.get("event_key"), "event")


def status_label(value) -> str:
    labels = {
        "announced": "已宣布",
        "in_progress": "进行中",
        "ongoing": "进行中",
        "completed": "已完成",
        "closed": "已结束",
        "paused": "已暂停",
    }
    raw = str(value or "")
    return labels.get(raw, raw or "未标注")


def layout(title: str, body: str, depth: int = 0) -> str:
    prefix = "../" * depth
    nav = (
        f'<a href="{prefix}index.html">首页</a>'
        f'<a href="{prefix}events.html">事件数据库</a>'
        f'<a href="{prefix}rss.xml">RSS</a>'
    )
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{safe_text(title)}</title><meta name="description" content="{safe_text(SITE_DESCRIPTION)}"><style>{STYLE}</style></head><body><header class="top"><div class="wrap"><a class="brand" href="{prefix}index.html">{SITE_TITLE}</a><nav class="nav">{nav}</nav></div></header><main class="wrap">{body}</main><footer class="wrap footer">全球家电AI早报 · 公开资讯 · 北京时间</footer></body></html>"""


def render_item(item: dict, date_key: str, index: int, prefix: str = "") -> str:
    title = safe_text(item.get("title"))
    excerpt = safe_text(item.get("excerpt"))
    source = safe_text(item.get("source_name"))
    sources = extract_original_sources(item)
    published_date = fmt_public_date_cn(item.get("source_published_date") or fmt_day(date_key))
    collected_date = fmt_public_date_cn(date_key)
    meta_date = safe_text(f"{collected_date}（发布于{published_date}）")
    slug = article_slug(item, date_key, index)
    detail_url = f"{prefix}articles/{slug}/index.html"
    event = item.get("event") if isinstance(item.get("event"), dict) else None
    action = item.get("event_action") or "none"
    badge = ""
    event_jump = ""
    if action in {"create", "update"}:
        badge_text = "新增事件" if action == "create" else "事件更新"
        badge = f'<span class="pill">{badge_text}</span>'
    if event and event.get("event_key"):
        event_jump = f'<a class="event-link" href="{prefix}events/{event_slug(event)}/index.html">查看关联事件 →</a>'
    source_link = ""
    if sources:
        label = f"原始来源（{len(sources)}） ↗" if len(sources) > 1 else "原始来源 ↗"
        primary_url = html.escape(sources[0][0], quote=True)
        source_link = f'<a class="source" href="{primary_url}" target="_blank" rel="noopener noreferrer">{label}</a>'
    return f'''<article class="card news"><h2><a class="item-title" href="{detail_url}">{title}</a></h2><div class="meta">{meta_date} · {source} {badge}</div><div class="excerpt">{excerpt}</div><div class="item-actions"><a class="text-link" href="{detail_url}">查看详情 →</a>{event_jump}{source_link}</div></article>'''


def collect_events(batches):
    events = {}
    for date_key, batch in batches:
        for index, item in enumerate(batch.get("items", [])):
            event = item.get("event")
            if not isinstance(event, dict):
                continue
            key = event.get("event_key")
            if not key:
                continue
            record = events.setdefault(key, {"snapshot": {}, "related": []})
            snapshot = dict(event)
            snapshot["last_seen_batch"] = date_key
            snapshot["last_item_title"] = item.get("title", "")
            record["snapshot"] = snapshot
            record["related"].append((date_key, index, item))
            info_date = str(item.get("source_published_date") or fmt_day(date_key))
            if info_date > record.get("latest_info_date", ""):
                record["latest_info_date"] = info_date
    return events


def build_archive_sidebar(batches):
    months = {}
    for date_key, batch in reversed(batches):
        months.setdefault(date_key[:6], []).append((date_key, len(batch.get("items", []))))
    current_month = batches[-1][0][:6] if batches else ""
    groups = []
    for month_key, days in months.items():
        open_attr = " open" if month_key == current_month else ""
        links = "".join(
            f'<li><a href="daily/{date_key}/index.html"><span>{fmt_day_cn(date_key)}</span><span class="day-count">{count}条</span></a></li>'
            for date_key, count in days
        )
        groups.append(
            f'<details class="month"{open_attr}><summary>{fmt_month_cn(month_key)}</summary><ul class="day-list">{links}</ul></details>'
        )
    return f'''<div class="card archive-panel"><h3>每日早报</h3>{"".join(groups)}<a class="all-link" href="archive.html">查看全部早报 →</a></div>'''


def build_event_sidebar(events):
    ordered = sorted(
        events.values(),
        key=lambda record: record.get("latest_info_date", ""),
        reverse=True,
    )
    links = []
    for record in ordered:
        e = record["snapshot"]
        links.append(
            f'''<li><a href="events/{event_slug(e)}/index.html"><div class="sidebar-event-title">{safe_text(e.get("title"))}</div><div class="sidebar-event-date">最新资讯：{safe_text(record.get("latest_info_date") or fmt_day(e.get("last_seen_batch", "")))}</div></a></li>'''
        )
    return f'''<div class="card sidebar-events"><h3>事件</h3><ul class="sidebar-event-list">{"".join(links)}</ul><a class="all-link" href="events.html">查看全部事件 →</a></div>'''


def build_home(batches):
    if not batches:
        body = '<section class="hero"><h1>全球家电AI早报</h1><p class="sub">暂无公开批次数据。</p></section>'
        return layout(SITE_TITLE, body)
    latest_key, latest = batches[-1]
    recent = []
    for date_key, batch in reversed(batches):
        items = batch.get("items", [])
        for index in range(len(items) - 1, -1, -1):
            recent.append((date_key, index, items[index]))
            if len(recent) >= 20:
                break
        if len(recent) >= 20:
            break
    events = collect_events(batches)
    total_items = sum(len(b.get("items", [])) for _, b in batches)
    items_html = "".join(render_item(item, date_key, index) for date_key, index, item in recent)
    archive_sidebar = build_archive_sidebar(batches)
    event_sidebar = build_event_sidebar(events)
    body = f'''<section class="hero"><div class="hero-dashboard"><div class="hero-main"><h1>{SITE_TITLE}</h1><p class="sub">最新公开批次：{fmt_day(latest_key)} · 当日 {len(latest.get("items", []))} 条资讯</p></div><aside class="stats-box"><div class="stats-label">公开数据概况</div><div class="stats-row"><div class="stat-item"><div class="stat">{total_items}</div><div class="stat-name">累计资讯</div></div><div class="stat-item"><div class="stat">{len(batches)}</div><div class="stat-name">早报批次</div></div><div class="stat-item"><div class="stat">{len(events)}</div><div class="stat-name">持续事件</div></div></div></aside></div></section><div class="home-grid"><aside class="archive-side">{archive_sidebar}{event_sidebar}</aside><section id="latest"><h2 class="section-title">最新资讯</h2>{items_html}</section></div>'''
    return layout(SITE_TITLE, body)


def build_archive(batches):
    cards = []
    for date_key, batch in reversed(batches):
        cards.append(f'''<a class="card" href="daily/{date_key}/index.html"><strong>{fmt_day(date_key)}</strong><p class="sub">{len(batch.get("items", []))} 条资讯</p></a>''')
    body = f'''<section class="hero"><h1>每日早报</h1><p class="sub">按北京时间归档的公开资讯批次。</p></section><div class="archive-grid">{"".join(cards)}</div>'''
    return layout(f"每日早报 - {SITE_TITLE}", body)


def build_events(batches):
    events = collect_events(batches)
    ordered = sorted(events.items(), key=lambda kv: kv[1].get("latest_info_date", ""), reverse=True)
    cards = []
    for key, record in ordered:
        e = record["snapshot"]
        countries = "".join(f'<span class="pill">{safe_text(x)}</span>' for x in e.get("countries", []))
        category = f'<span class="pill">{safe_text(e.get("category"))}</span>' if e.get("category") else ""
        status = f'<span class="pill">{safe_text(status_label(e.get("status")))}</span>'
        cards.append(f'''<a class="event-card-link" href="events/{event_slug(e)}/index.html"><article class="card event"><h2>{safe_text(e.get("title"))}</h2><div>{category}{status}{countries}</div><p class="progress">{safe_text(e.get("latest_progress"))}</p><div class="meta">最新资讯：{safe_text(record.get("latest_info_date") or fmt_day(e.get("last_seen_batch", "")))} · 关联资讯 {len(record["related"])} 条</div></article></a>''')
    body = f'''<section class="hero"><h1>事件数据库</h1><p class="sub">点击任一事件可查看事件状态、最新进展及全部关联资讯。</p></section><div class="event-list">{"".join(cards) if cards else '<div class="empty">暂无事件数据。</div>'}</div>'''
    return layout(f"事件数据库 - {SITE_TITLE}", body)


def build_daily(date_key, batch):
    items = "".join(render_item(item, date_key, index, prefix="../../") for index, item in enumerate(batch.get("items", [])))
    body = f'''<section class="hero"><h1>{fmt_day(date_key)} 早报</h1><p class="sub">{len(batch.get("items", []))} 条公开资讯 · 生成时间 {safe_text(batch.get("generated_at_bjt", ""))}</p></section>{items}'''
    return layout(f"{fmt_day(date_key)} - {SITE_TITLE}", body, depth=2)


def build_article_detail(date_key, index, item):
    title = safe_text(item.get("title"))
    source = safe_text(item.get("source_name"))
    source_date = safe_text(item.get("source_published_date") or fmt_day(date_key))
    sources = extract_original_sources(item)
    content = sanitize_content_html(item.get("content_html"))
    if not content:
        content = f'<p>{safe_text(item.get("excerpt"))}</p>'
    source_section = ""
    if sources:
        source_rows = "".join(
            f'<li><a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{safe_text(label)}</a></li>'
            for url, label in sources
        )
        source_section = f'''<section class="detail-section"><h2>原始来源</h2><ul class="source-list">{source_rows}</ul></section>'''
    event = item.get("event") if isinstance(item.get("event"), dict) else None
    event_box = ""
    if event and event.get("event_key"):
        event_box = f'''<section class="detail-event"><h3>关联事件</h3><a class="event-link" href="../../events/{event_slug(event)}/index.html">{safe_text(event.get("title"))} →</a><p class="excerpt">{safe_text(event.get("latest_progress"))}</p></section>'''
    body = f'''<article class="detail-shell"><h1 class="detail-title">{title}</h1><div class="detail-meta"><span>{source_date}</span><span>{source}</span><span>收录日期：{fmt_day(date_key)}</span></div><div class="detail-content">{content}</div>{source_section}<div class="item-actions"><a class="text-link" href="../../daily/{date_key}/index.html">查看当日早报 →</a></div>{event_box}</article><p class="backline"><a href="../../index.html">← 返回首页</a></p>'''
    return layout(f"{item.get('title', '')} - {SITE_TITLE}", body, depth=2)


def build_event_detail(record):
    e = record["snapshot"]
    related = list(reversed(record["related"]))
    countries = "、".join(safe_text(x) for x in e.get("countries", [])) or "未标注"
    entities = "、".join(safe_text(x) for x in e.get("entities", [])) or "未标注"
    category = safe_text(e.get("category")) or "未标注"
    date_value = safe_text(e.get("date")) or "未标注"
    related_html = []
    for date_key, index, item in related:
        slug = article_slug(item, date_key, index)
        related_html.append(
            f'''<li class="related-item"><div class="related-date">{safe_text(item.get("source_published_date") or fmt_day(date_key))}</div><a class="related-title" href="../../articles/{slug}/index.html">{safe_text(item.get("title"))}</a><div class="related-excerpt">{safe_text(item.get("excerpt"))}</div></li>'''
        )
    body = f'''<article class="detail-shell"><h1 class="detail-title">{safe_text(e.get("title"))}</h1><div class="info-grid"><div class="info-box"><div class="info-label">事件日期</div><div class="info-value">{date_value}</div></div><div class="info-box"><div class="info-label">当前状态</div><div class="info-value">{safe_text(status_label(e.get("status")))}</div></div><div class="info-box"><div class="info-label">国家/地区</div><div class="info-value">{countries}</div></div><div class="info-box"><div class="info-label">涉及主体</div><div class="info-value">{entities}</div></div><div class="info-box"><div class="info-label">事件类别</div><div class="info-value">{category}</div></div><div class="info-box"><div class="info-label">关联资讯</div><div class="info-value">{len(related)} 条</div></div></div><section class="detail-section"><h2>最新进展</h2><div class="excerpt">{safe_text(e.get("latest_progress"))}</div></section><section class="detail-section"><h2>关联资讯</h2><ol class="related-list">{"".join(related_html)}</ol></section></article><p class="backline"><a href="../../events.html">← 返回事件数据库</a></p>'''
    return layout(f"{e.get('title', '')} - {SITE_TITLE}", body, depth=2)


def build_rss(batches):
    rss_open = (
        '<rss version="2.0" '
        'xmlns:content="http://purl.org/rss/1.0/modules/content/" '
        'xmlns:wfw="http://wellformedweb.org/CommentAPI/" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:atom="http://www.w3.org/2005/Atom" '
        'xmlns:sy="http://purl.org/rss/1.0/modules/syndication/" '
        'xmlns:slash="http://purl.org/rss/1.0/modules/slash/">'
    )
    feed_url = f"{SITE_URL}rss.xml"

    if not batches:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            + rss_open
            + '<channel>'
            + f'<title>{xml_escape(SITE_TITLE)}</title>'
            + f'<atom:link href="{xml_escape(feed_url)}" rel="self" type="application/rss+xml" />'
            + f'<link>{xml_escape(SITE_URL)}</link>'
            + f'<description>{xml_escape(SITE_DESCRIPTION)}</description>'
            + '<language>zh-CN</language>'
            + '<sy:updatePeriod>hourly</sy:updatePeriod>'
            + '<sy:updateFrequency>1</sy:updateFrequency>'
            + '</channel></rss>'
        )

    # RSS is synchronized to the newest public website batch. Same-day supplements
    # immediately appear in both the website and RSS in the same Pages deployment.
    date_key, batch = batches[-1]
    base_publish_time = batch_publish_time(date_key, batch)
    entries = []
    for index, item in enumerate(batch.get("items", [])):
        publish_time = (base_publish_time + timedelta(seconds=index)) if base_publish_time else None
        entries.append((publish_time, index, item))

    # Match WordPress RSS behavior: newest publication first.
    entries.sort(
        key=lambda row: row[0] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    entries = entries[:RSS_MAX_ITEMS]

    rows = []
    for publish_time, index, item in entries:
        title = xml_escape(str(item.get("title", "")))
        slug = article_slug(item, date_key, index)
        link_raw = f"{SITE_URL}articles/{slug}/"
        link = xml_escape(link_raw)
        guid = xml_escape(str(item.get("public_id") or link_raw))
        category = "行业资讯"
        event = item.get("event")
        if isinstance(event, dict) and event.get("category"):
            category = str(event.get("category"))

        description = rss_description_html(item)
        full_content = rss_content_html(item)
        pub_xml = f"<pubDate>{xml_escape(rss_pubdate(publish_time))}</pubDate>" if publish_time else ""

        rows.append(
            '<item>'
            f'<title>{title}</title>'
            f'<link>{link}</link>'
            f'<dc:creator>{cdata(RSS_AUTHOR)}</dc:creator>'
            f'{pub_xml}'
            f'<category>{cdata(category)}</category>'
            f'<guid isPermaLink="false">{guid}</guid>'
            f'<description>{cdata(description)}</description>'
            f'<content:encoded>{cdata(full_content)}</content:encoded>'
            '</item>'
        )

    last_build = entries[0][0] if entries else base_publish_time
    channel_description = SITE_DESCRIPTION
    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        + rss_open
        + '<channel>'
        + f'<title>{xml_escape(SITE_TITLE)}</title>'
        + f'<atom:link href="{xml_escape(feed_url)}" rel="self" type="application/rss+xml" />'
        + f'<link>{xml_escape(SITE_URL)}</link>'
        + f'<description>{xml_escape(channel_description)}</description>'
        + (f'<lastBuildDate>{xml_escape(rss_pubdate(last_build))}</lastBuildDate>' if last_build else '')
        + '<language>zh-CN</language>'
        + '<sy:updatePeriod>hourly</sy:updatePeriod>'
        + '<sy:updateFrequency>1</sy:updateFrequency>'
        + "".join(rows)
        + '</channel></rss>'
    )
    print(f"RSS synchronized to latest public batch: {date_key} ({len(entries)} items), WordPress-compatible RSS2")
    return rss


def main():
    batches = load_batches()
    events = collect_events(batches)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "index.html").write_text(build_home(batches), encoding="utf-8")
    (OUT / "archive.html").write_text(build_archive(batches), encoding="utf-8")
    (OUT / "events.html").write_text(build_events(batches), encoding="utf-8")
    (OUT / "rss.xml").write_text(build_rss(batches), encoding="utf-8")

    data_dir = OUT / "data"
    data_dir.mkdir()
    latest = batches[-1][1] if batches else {"items": []}
    (data_dir / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8")

    article_count = 0
    for date_key, batch in batches:
        daily_dir = OUT / "daily" / date_key
        daily_dir.mkdir(parents=True, exist_ok=True)
        (daily_dir / "index.html").write_text(build_daily(date_key, batch), encoding="utf-8")
        for index, item in enumerate(batch.get("items", [])):
            slug = article_slug(item, date_key, index)
            article_dir = OUT / "articles" / slug
            article_dir.mkdir(parents=True, exist_ok=True)
            (article_dir / "index.html").write_text(build_article_detail(date_key, index, item), encoding="utf-8")
            article_count += 1

    for _, record in events.items():
        slug = event_slug(record["snapshot"])
        event_dir = OUT / "events" / slug
        event_dir.mkdir(parents=True, exist_ok=True)
        (event_dir / "index.html").write_text(build_event_detail(record), encoding="utf-8")

    print(f"Built {len(batches)} batches, {article_count} articles and {len(events)} events into {OUT}")


if __name__ == "__main__":
    main()
