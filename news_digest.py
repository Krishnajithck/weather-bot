import os
import requests
import smtplib
from bs4 import BeautifulSoup
from datetime import datetime
from email.message import EmailMessage

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
        html = fetch_html("https://www.bbc.com/news")
        soup = BeautifulSoup(html, "html.parser")
        headlines = []
        
        # Try multiple selectors for BBC
        selectors = [
            "a.sc-4fedabbc-3",  # BBC news link class
            "a[data-testid='internal-link']",  # BBC internal links
            "h2 a",  # Generic h2 links
            "h3 a",  # Generic h3 links
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links[:5]:
                title = link.get_text(strip=True)
                href = link.get("href")
                if not href or not title or len(title) < 5:
                    continue
                if href.startswith("/"):
                    href = f"https://www.bbc.com{href}"
                if "bbc.com" in href:
                    headlines.append({"source": "BBC News", "title": title, "url": href})
            if headlines:
                break
        
        return headlines[:5]
    except Exception as e:
        print(f"BBC parsing error: {e}")
        return []


def parse_cnn():
    try:
        html = fetch_html("https://edition.cnn.com")
        soup = BeautifulSoup(html, "html.parser")
        headlines = []
        
        # Try multiple selectors for CNN
        selectors = [
            "span.container__headline-text",  # CNN headline text
            "a.container__link",  # CNN container links
            "h3 a",  # Generic h3 links
            "a[data-link-type='story-link']",  # Story links
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links[:5]:
                title = link.get_text(strip=True)
                href = link.get("href") if link.name == "a" else link.parent.get("href")
                if not href or not title or len(title) < 5:
                    continue
                if href.startswith("/"):
                    href = f"https://edition.cnn.com{href}"
                if "cnn.com" in href:
                    headlines.append({"source": "CNN", "title": title, "url": href})
            if headlines:
                break
        
        return headlines[:5]
    except Exception as e:
        print(f"CNN parsing error: {e}")
        return []


def parse_techcrunch():
    try:
        html = fetch_html("https://techcrunch.com")
        soup = BeautifulSoup(html, "html.parser")
        headlines = []
        
        # Try multiple selectors for TechCrunch
        selectors = [
            "a.post-block__title__link",  # Original selector
            "h2.post-block__title a",  # Alternative h2 links
            "a.post-block__content__link",  # Content links
            "h3 a",  # Generic h3 links
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links[:5]:
                title = link.get_text(strip=True)
                href = link.get("href")
                if not href or not title or len(title) < 5:
                    continue
                headlines.append({"source": "TechCrunch", "title": title, "url": href})
            if headlines:
                break
        
        return headlines[:5]
    except Exception as e:
        print(f"TechCrunch parsing error: {e}")
        return []


def fetch_published_at(url):
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        if meta := soup.find("meta", attrs={"property": "article:published_time"}):
            return meta.get("content")
        if time_tag := soup.find("time"):
            return time_tag.get("datetime") or time_tag.get_text(strip=True)
    except Exception:
        return None
    return None


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
        published = item.get("published_at") or "Unknown"
        html_body.append(
            "<tr>"
            f"<td style='vertical-align: top; padding: 8px; border-bottom: 1px solid #eee;'>{item['source']}</td>"
            f"<td style='vertical-align: top; padding: 8px; border-bottom: 1px solid #eee;'><a href=\"{item['url']}\">{item['title']}</a></td>"
            f"<td style='vertical-align: top; padding: 8px; border-bottom: 1px solid #eee;'>{published}</td>"
            "</tr>"
        )

    html_body.append("</tbody></table>")
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

    # Log what was found
    print(f"Found {len(sources)} headlines total")
    for source in sources:
        print(f"  - {source['source']}: {source['title'][:50]}...")

    if not sources:
        print("WARNING: No headlines found from any source!")
        # Create a fallback message
        sources = [
            {
                "source": "System",
                "title": "No news headlines could be retrieved at this time",
                "url": "https://www.bbc.com/news",
                "published_at": datetime.utcnow().isoformat() + "Z"
            }
        ]

    for item in sources:
        if "published_at" not in item:
            item["published_at"] = fetch_published_at(item["url"]) or "Unknown"

    email_html = build_email(sources)
    subject = "Daily News Digest — BBC, CNN, TechCrunch"

    try:
        send_email(subject, email_html)
        print("News digest email sent successfully.")
    except Exception as error:
        print(f"Failed to send email: {error}")
        raise
