import os
import requests
import smtplib
import feedparser
from datetime import datetime
from email.message import EmailMessage
from urllib.parse import urlparse

EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "krishnajith.ck.dev@gmail.com")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT", "krishnajithck123@gmail.com")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")


def fetch_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.text


def parse_bbc():
    try:
        feed_url = "https://feeds.bbci.co.uk/news/rss.xml"
        feed = feedparser.parse(feed_url)
        headlines = []
        
        for entry in feed.entries[:5]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            
            if not title or not link or len(title) < 5:
                continue
            
            headlines.append({
                "source": "BBC News",
                "title": title,
                "url": link,
                "published_at": entry.get("published", "Unknown")
            })
        
        print(f"BBC: Found {len(headlines)} headlines")
        return headlines
    except Exception as e:
        print(f"BBC RSS parsing error: {e}")
        return []


def parse_cnn():
    try:
        feed_url = "https://feeds.cnn.com/rss/edition.rss"
        feed = feedparser.parse(feed_url)
        headlines = []
        
        for entry in feed.entries[:5]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            
            if not title or not link or len(title) < 5:
                continue
            
            headlines.append({
                "source": "CNN",
                "title": title,
                "url": link,
                "published_at": entry.get("published", "Unknown")
            })
        
        print(f"CNN: Found {len(headlines)} headlines")
        return headlines
    except Exception as e:
        print(f"CNN RSS parsing error: {e}")
        return []


def parse_techcrunch():
    try:
        feed_url = "https://techcrunch.com/feed/"
        feed = feedparser.parse(feed_url)
        headlines = []
        
        for entry in feed.entries[:5]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            
            if not title or not link or len(title) < 5:
                continue
            
            headlines.append({
                "source": "TechCrunch",
                "title": title,
                "url": link,
                "published_at": entry.get("published", "Unknown")
            })
        
        print(f"TechCrunch: Found {len(headlines)} headlines")
        return headlines
    except Exception as e:
        print(f"TechCrunch RSS parsing error: {e}")
        return []


def build_email(headlines):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    html_body = [
        f"<h1>Daily News Digest</h1>",
        f"<p>Generated at {now}</p>",
        "<table style='width:100%; border-collapse: collapse;'>",
        "<thead><tr><th style='text-align:left; border-bottom: 2px solid #ddd;'>Source</th><th style='text-align:left; border-bottom: 2px solid #ddd;'>Headline</th><th style='text-align:left; border-bottom: 2px solid #ddd;'>Published</th></tr></thead>",
        "<tbody>",
    ]

    for item in headlines:
        published = item.get("published_at", "Unknown")
        # Clean up the published date if it's an ISO timestamp
        if isinstance(published, str) and "T" in published:
            try:
                published = published.split("T")[0]  # Just keep the date part
            except:
                pass
        
        html_body.append(
            "<tr>"
            f"<td style='vertical-align: top; padding: 8px; border-bottom: 1px solid #eee;'><strong>{item['source']}</strong></td>"
            f"<td style='vertical-align: top; padding: 8px; border-bottom: 1px solid #eee;'><a href=\"{item['url']}\" style='color: #007bff; text-decoration: none;'>{item['title']}</a></td>"
            f"<td style='vertical-align: top; padding: 8px; border-bottom: 1px solid #eee;'>{published}</td>"
            "</tr>"
        )

    html_body.append("</tbody></table>")
    html_body.append("<hr style='margin-top: 20px; border: none; border-top: 1px solid #ddd;'>")
    html_body.append("<p style='font-size: 12px; color: #999;'>This is an automated daily news digest. Powered by RSS feeds.</p>")
    return "\n".join(html_body)


def send_email(subject, html_content):
    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError("SMTP_USER and SMTP_PASSWORD environment variables are required.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = EMAIL_SENDER
    message["To"] = EMAIL_RECIPIENT
    message.set_content("Your email client does not support HTML email.")
    message.add_alternative(html_content, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(message)


if __name__ == "__main__":
    sources = []
    sources.extend(parse_bbc())
    sources.extend(parse_cnn())
    sources.extend(parse_techcrunch())

    print(f"Total headlines found: {len(sources)}")

    if not sources:
        print("WARNING: No headlines found from any RSS feed!")
        # Create a fallback message
        sources = [
            {
                "source": "System",
                "title": "No news headlines could be retrieved at this time. Check RSS feeds availability.",
                "url": "https://www.bbc.com/news",
                "published_at": datetime.utcnow().isoformat() + "Z"
            }
        ]

    email_html = build_email(sources)
    subject = "Daily News Digest — BBC, CNN, TechCrunch"

    try:
        send_email(subject, email_html)
        print("News digest email sent successfully.")
    except Exception as error:
        print(f"Failed to send email: {error}")
        raise
