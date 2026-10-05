#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import shutil
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = ROOT / "public-batches"
OUT = ROOT / "_site"
SITE_TITLE = "全球家电AI早报"
SITE_DESCRIPTION = "全球家电、贸易政策、供应链与制造布局公开资讯"

STYLE = """
:root{color-scheme:light;--bg:#f6f7f9;--card:#fff;--text:#18202a;--muted:#667085;--line:#e5e7eb;--accent:#0f62fe;--max:1120px}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text)}a{color:inherit;text-decoration:none}.wrap{max-width:var(--max);margin:auto;padding:0 20px}.top{background:#0d1b2a;color:white}.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:24px;padding-top:18px;padding-bottom:18px}.brand{font-weight:800;font-size:22px}.nav{display:flex;gap:18px;font-size:14px;opacity:.92}.hero{padding:38px 0 24px}.hero h1{font-size:34px;margin:0 0 10px}.sub{color:var(--muted);line-height:1.7}.grid{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:24px}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;margin-bottom:16px}.news h2{font-size:21px;line-height:1.45;margin:0 0 10px}.meta{font-size:13px;color:var(--muted);margin-bottom:10px}.excerpt{line-height:1.75;color:#344054}.source{font-size:13px;color:var(--accent)}.pill{display:inline-block;padding:4px 9px;border:1px solid var(--line);border-radius:999px;font-size:12px;color:#475467;margin:3px 4px 3px 0}.side h3,.section-title{margin:0 0 14px}.stat{font-size:30px;font-weight:800}.list{padding:0;margin:0;list-style:none}.list li{padding:10px 0;border-bottom:1px solid var(--line)}.archive-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}.event h2{font-size:19px;margin:0 0 10px}.event .progress{line-height:1.7;color:#344054}.footer{color:var(--muted);font-size:13px;padding:34px 0 48px}.empty{padding:40px 0;color:var(--muted)}@media(max-width:800px){.grid{grid-template-columns:1fr}.nav{gap:10px;font-size:13px}.top .wrap{align-items:flex-start;flex-direction:column}.hero h1{font-size:28px}}
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


def safe_text(value) -> str:
    return html.escape(str(value or ""))


def layout(title: str, body: str, depth: int = 0) -> str:
    prefix = "../" * depth
    nav = (
        f'<a href="{prefix}index.html">首页</a>'
        f'<a href="{prefix}archive.html">每日早报</a>'
        f'<a href="{prefix}events.html">事件数据库</a>'
        f'<a href="{prefix}rss.xml">RSS</a>'
    )
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{safe_text(title)}</title><meta name="description" content="{safe_text(SITE_DESCRIPTION)}"><style>{STYLE}</style></head><body><header class="top"><div class="wrap"><a class="brand" href="{prefix}index.html">{SITE_TITLE}</a><nav class="nav">{nav}</nav></div></header><main class="wrap">{body}</main><footer class="wrap footer">全球家电AI早报 · 公开资讯 · 北京时间</footer></body></html>"""


def render_item(item: dict) -> str:
    title = safe_text(item.get("title"))
    excerpt = safe_text(item.get("excerpt"))
    source = safe_text(item.get("source_name"))
    source_url = safe_text(item.get("source_url"))
    date = safe_text(item.get("source_published_date"))
    action = item.get("event_action") or "none"
    badge = ""
    if action in {"create", "update"}:
        badge = f'<span class="pill">事件{safe_text(action)}</span>'
    return f'''<article class="card news"><h2>{title}</h2><div class="meta">{date} · {source} {badge}</div><div class="excerpt">{excerpt}</div><p><a class="source" href="{source_url}" target="_blank" rel="noopener noreferrer">查看原始来源 →</a></p></article>'''


def collect_events(batches):
    events = {}
    for date_key, batch in batches:
        for item in batch.get("items", []):
            event = item.get("event")
            if not isinstance(event, dict):
                continue
            key = event.get("event_key")
            if not key:
                continue
            snapshot = dict(event)
            snapshot["last_seen_batch"] = date_key
            snapshot["last_item_title"] = item.get("title", "")
            events[key] = snapshot
    return events


def build_home(batches):
    if not batches:
        body = '<section class="hero"><h1>全球家电AI早报</h1><p class="sub">暂无公开批次数据。</p></section>'
        return layout(SITE_TITLE, body)
    latest_key, latest = batches[-1]
    recent = []
    for date_key, batch in reversed(batches):
        for item in reversed(batch.get("items", [])):
            recent.append((date_key, item))
            if len(recent) >= 20:
                break
        if len(recent) >= 20:
            break
    events = collect_events(batches)
    items_html = "".join(render_item(item) for _, item in recent)
    body = f'''<section class="hero"><h1>{SITE_TITLE}</h1><p class="sub">最新公开批次：{fmt_day(latest_key)} · 共 {len(latest.get("items", []))} 条资讯。当前为 GitHub Pages 公开站测试版。</p></section><div class="grid"><section><h2 class="section-title">最新资讯</h2>{items_html}</section><aside class="side"><div class="card"><h3>公开数据概况</h3><div class="stat">{sum(len(b.get("items", [])) for _, b in batches)}</div><div class="sub">累计公开资讯</div><p><span class="pill">{len(batches)} 个批次</span><span class="pill">{len(events)} 个事件</span></p></div><div class="card"><h3>最新批次</h3><div>{fmt_day(latest_key)}</div><p class="sub">{safe_text(latest.get("generated_at_bjt", ""))}</p><a class="source" href="daily/{latest_key}/index.html">查看当日全部资讯 →</a></div></aside></div>'''
    return layout(SITE_TITLE, body)


def build_archive(batches):
    cards = []
    for date_key, batch in reversed(batches):
        cards.append(f'''<a class="card" href="daily/{date_key}/index.html"><strong>{fmt_day(date_key)}</strong><p class="sub">{len(batch.get("items", []))} 条资讯</p></a>''')
    body = f'''<section class="hero"><h1>每日早报</h1><p class="sub">按北京时间归档的公开资讯批次。</p></section><div class="archive-grid">{"".join(cards)}</div>'''
    return layout(f"每日早报 - {SITE_TITLE}", body)


def build_events(batches):
    events = collect_events(batches)
    ordered = sorted(events.values(), key=lambda e: e.get("last_seen_batch", ""), reverse=True)
    cards = []
    for e in ordered:
        countries = "".join(f'<span class="pill">{safe_text(x)}</span>' for x in e.get("countries", []))
        category = f'<span class="pill">{safe_text(e.get("category"))}</span>' if e.get("category") else ""
        status = f'<span class="pill">{safe_text(e.get("status"))}</span>' if e.get("status") else ""
        cards.append(f'''<article class="card event"><h2>{safe_text(e.get("title"))}</h2><div>{category}{status}{countries}</div><p class="progress">{safe_text(e.get("latest_progress"))}</p><div class="meta">event_key: {safe_text(e.get("event_key"))} · 最后更新批次 {fmt_day(e.get("last_seen_batch", ""))}</div></article>''')
    body = f'''<section class="hero"><h1>事件数据库</h1><p class="sub">由每日公开批次中的 create / update 事件快照聚合，展示最新状态。</p></section>{"".join(cards) if cards else '<div class="empty">暂无事件数据。</div>'}'''
    return layout(f"事件数据库 - {SITE_TITLE}", body)


def build_daily(date_key, batch):
    items = "".join(render_item(item) for item in batch.get("items", []))
    body = f'''<section class="hero"><h1>{fmt_day(date_key)} 早报</h1><p class="sub">{len(batch.get("items", []))} 条公开资讯 · 生成时间 {safe_text(batch.get("generated_at_bjt", ""))}</p></section>{items}'''
    return layout(f"{fmt_day(date_key)} - {SITE_TITLE}", body, depth=2)


def build_rss(batches):
    entries = []
    for date_key, batch in reversed(batches):
        for item in reversed(batch.get("items", [])):
            entries.append((date_key, item))
            if len(entries) >= 50:
                break
        if len(entries) >= 50:
            break
    rows = []
    for date_key, item in entries:
        title = xml_escape(str(item.get("title", "")))
        link = xml_escape(str(item.get("source_url", "")))
        desc = xml_escape(str(item.get("excerpt", "")))
        guid = xml_escape(str(item.get("public_id", link)))
        pub = xml_escape(str(item.get("source_published_date", fmt_day(date_key))))
        rows.append(f"<item><title>{title}</title><link>{link}</link><guid>{guid}</guid><description>{desc}</description><pubDate>{pub}</pubDate></item>")
    return f'''<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{xml_escape(SITE_TITLE)}</title><description>{xml_escape(SITE_DESCRIPTION)}</description><link>https://superke7.github.io/global-appliance-intelligence-web/</link>{''.join(rows)}</channel></rss>'''


def main():
    batches = load_batches()
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
    for date_key, batch in batches:
        daily_dir = OUT / "daily" / date_key
        daily_dir.mkdir(parents=True, exist_ok=True)
        (daily_dir / "index.html").write_text(build_daily(date_key, batch), encoding="utf-8")
    print(f"Built {len(batches)} batches into {OUT}")


if __name__ == "__main__":
    main()
