"""
Weekly digest generator.
Queries top-5 interpreted items per category (last 7 days, sorted by relevance).
Saves HTML to weekly_data_reports table.
Emails via SendGrid if SENDGRID_API_KEY is set.

Run: python processors/weekly_digest.py [--dry-run] [--email you@example.com]
Scheduled: GitHub Actions every Monday 07:30 UTC
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from db.client import supabase

CATEGORIES = [
    ("news",               "News & Updates",        "📰"),
    ("competitors",        "Competitors",            "🏢"),
    ("crop_recommendations", "Crop Recommendations", "🌱"),
    ("patents",            "Patents",                "📋"),
    ("regulations",        "Regulations",            "⚖️"),
    ("genetics",           "Genetics",               "🧬"),
]


def load_top_items(category_slug: str, since_iso: str, limit: int = 5):
    resp = supabase.table("interpreted_items").select(
        "title_en, summary_en, relevance_score, tags, category_slug, "
        "scraped_items(url, published_at, language, source_id)"
    ).eq("category_slug", category_slug) \
     .gte("interpreted_at", since_iso) \
     .order("relevance_score", desc=True) \
     .limit(limit) \
     .execute()
    return resp.data or []


def safe(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_item_html(item: dict) -> str:
    si = item.get("scraped_items") or {}
    title = safe(item.get("title_en") or si.get("title") or "(untitled)")
    summary = safe(item.get("summary_en") or "")
    url = si.get("url") or "#"
    score = item.get("relevance_score") or 0
    tags = item.get("tags") or []
    date = si.get("published_at", "")[:10] if si.get("published_at") else ""
    score_color = "#16a34a" if score >= 7 else "#ca8a04" if score >= 4 else "#9ca3af"
    tag_html = "".join(
        f'<span style="background:#f3f4f6;color:#4b5563;border-radius:4px;padding:1px 6px;font-size:11px;margin-right:4px">{safe(t)}</span>'
        for t in tags[:4]
    )
    return f"""
    <div style="margin-bottom:16px;padding:14px;background:#fff;border:1px solid #e5e7eb;border-radius:8px">
      <a href="{url}" style="font-weight:600;color:#111827;font-size:13px;text-decoration:none;display:block;margin-bottom:4px">{title}</a>
      {f'<p style="font-size:12px;color:#4b5563;margin:0 0 6px;line-height:1.5">{summary}</p>' if summary else ''}
      <div style="font-size:11px;color:#9ca3af">
        {date} · <span style="color:{score_color};font-weight:600">{score}/10</span>
        {f" · {tag_html}" if tag_html else ""}
      </div>
    </div>"""


def render_category_html(label: str, icon: str, items: list) -> str:
    if not items:
        return ""
    items_html = "".join(render_item_html(i) for i in items)
    return f"""
    <div style="margin-bottom:32px">
      <h2 style="font-size:15px;font-weight:700;color:#111827;margin:0 0 12px;padding-bottom:8px;border-bottom:2px solid #f3f4f6">
        {icon} {label}
      </h2>
      {items_html}
    </div>"""


def generate_digest(dry_run: bool = False, email: str = None):
    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    week_label = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%b %d") + \
                 " – " + datetime.now(timezone.utc).strftime("%b %d, %Y")

    print(f"[weekly_digest] Generating digest for {week_label}")

    sections_html = ""
    summary_data = {}

    for slug, label, icon in CATEGORIES:
        items = load_top_items(slug, week_start)
        print(f"  {icon} {label}: {len(items)} items")
        summary_data[slug] = [
            {
                "title": i.get("title_en"),
                "url": (i.get("scraped_items") or {}).get("url"),
                "score": i.get("relevance_score"),
                "tags": i.get("tags") or [],
            }
            for i in items
        ]
        if items:
            sections_html += render_category_html(label, icon, items)

    total_items = sum(len(v) for v in summary_data.values())

    if not sections_html:
        print("[weekly_digest] No items found — skipping digest generation.")
        return

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tomato Intel Weekly · {today}</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:640px;margin:0 auto;padding:24px;color:#111827;background:#f9fafb">
  <div style="background:#fff;border-radius:12px;padding:24px;border:1px solid #e5e7eb">
    <div style="margin-bottom:24px;padding-bottom:16px;border-bottom:2px solid #f3f4f6">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
        <span style="font-size:22px">🍅</span>
        <span style="font-size:18px;font-weight:700;color:#111827">Tomato Intel</span>
      </div>
      <p style="font-size:13px;color:#6b7280;margin:0">Weekly Intelligence Digest · {week_label}</p>
      <p style="font-size:12px;color:#9ca3af;margin:4px 0 0">{total_items} top articles across {len([s for s in summary_data if summary_data[s]])} categories</p>
    </div>

    {sections_html}

    <div style="margin-top:24px;padding-top:16px;border-top:1px solid #f3f4f6;font-size:11px;color:#9ca3af;text-align:center">
      Generated by Tomato Intel · <a href="https://tomato-intel.vercel.app" style="color:#16a34a">Open Dashboard</a>
    </div>
  </div>
</body></html>"""

    if dry_run:
        print(f"[weekly_digest] DRY RUN — HTML ({len(html)} chars) not saved.")
        print(html[:500])
        return

    # Save to weekly_data_reports
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        supabase.table("weekly_data_reports").upsert({
            "date": today_date,
            "news_data": json.dumps(summary_data.get("news", [])),
            "technical_data": json.dumps({
                "patents": summary_data.get("patents", []),
                "genetics": summary_data.get("genetics", []),
            }),
            "social_media_data": json.dumps(summary_data.get("social", [])),
            "digest_html": html,
        }, on_conflict="date").execute()
        print(f"[weekly_digest] Saved to weekly_data_reports for {today_date}")
    except Exception as e:
        print(f"[weekly_digest] Could not save to DB: {e} (table may not have digest_html column yet)")

    # Email via SendGrid if configured
    sendgrid_key = os.environ.get("SENDGRID_API_KEY")
    if sendgrid_key and email:
        send_email(sendgrid_key, email, f"Tomato Intel Weekly · {today}", html)
    elif email and not sendgrid_key:
        print("[weekly_digest] SENDGRID_API_KEY not set — email skipped.")

    print("[weekly_digest] Done.")


def send_email(api_key: str, to: str, subject: str, html: str):
    payload = json.dumps({
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": "digest@tomato-intel.io", "name": "Tomato Intel"},
        "subject": subject,
        "content": [{"type": "text/html", "value": html}],
    }).encode()
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"[weekly_digest] Email sent to {to} — status {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"[weekly_digest] Email failed: {e.code} {e.read().decode()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--email", type=str, default=None, help="Send digest to this email address")
    args = parser.parse_args()
    generate_digest(dry_run=args.dry_run, email=args.email)
