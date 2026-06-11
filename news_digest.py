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
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.text


def parse_bbc():
    html = fetch_html("https://www.bbc.com/news")
    soup = BeautifulSoup(html, "html.parser")
    headlines = []
    for link in soup.select("a.gs-c-promo-heading")[:5]:
        title = link.get_text(strip=True)
        href = link.get("href")
        if not href:
            continue
        if href.startswith("/"):
            href = f"https://www.bbc.com{href}"
        headlines.append({"source": "BBC News", "title": title, "url": href})
    return headlines


def parse_cnn():
    html = fetch_html("https://edition.cnn.com")
    soup = BeautifulSoup(html, "html.parser")
    headlines = []
    for item in soup.select("h3.cd__headline a")[:5]:
        title = item.get_text(strip=True)
        href = item.get("href")
        if not href:
            continue
        if href.startswith("/"):
            href = f"https://edition.cnn.com{href}"
        headlines.append({"source": "CNN", "title": title, "url": href})
    return headlines


def parse_techcrunch():
    html = fetch_html("https://techcrunch.com")
    soup = BeautifulSoup(html, "html.parser")
    headlines = []
    for item in soup.select("a.post-block__title__link")[:5]:
        title = item.get_text(strip=True)
        href = item.get("href")
        if not href:
            continue
        headlines.append({"source": "TechCrunch", "title": title, "url": href})
    return headlines


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

    for item in sources:
        item["published_at"] = fetch_published_at(item["url"]) or "Unknown"

    email_html = build_email(sources)
    subject = "Daily News Digest — BBC, CNN, TechCrunch"

    try:
        send_email(subject, email_html)
        print("News digest email sent successfully.")
    except Exception as error:
        print(f"Failed to send email: {error}")
        raise
