import html
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

import requests


FEED_URL = (
    "https://rss-bridge.org/bridge01/"
    "?action=display"
    "&bridge=InstagramBridge"
    "&context=Username"
    "&u=yamasaki.ten"
    "&media_type=all"
    "&format=Atom"
)

WEBHOOK_URL = os.environ.get("WEBHOOK_TEST_TEN", "").strip()

NS = {
    "atom": "http://www.w3.org/2005/Atom",
}


def clean_text(value):
    if not value:
        return ""

    value = html.unescape(value)
    value = re.sub(r"<brs*/?>", "
", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"
{3,}", "

", value)

    return value.strip()


def get_text(parent, name):
    node = parent.find("atom:" + name, NS)

    if node is None:
        return ""

    text = "".join(node.itertext())
    return clean_text(text)


def get_post_url(entry):
    for node in entry.findall("atom:link", NS):
        href = node.attrib.get("href", "")
        rel = node.attrib.get("rel", "")
        link_type = node.attrib.get("type", "")

        if rel == "alternate" and href:
            return href

        if link_type == "text/html" and href:
            return href

    return ""


def get_images(entry):
    images = []

    for node in entry.findall("atom:link", NS):
        rel = node.attrib.get("rel", "")
        link_type = node.attrib.get("type", "")
        href = node.attrib.get("href", "")

        if rel == "enclosure" and link_type.startswith("image/") and href:
            if href not in images:
                images.append(href)

    return images


def format_time(value):
    if not value:
        return ""

    try:
        date_value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return date_value.astimezone().strftime("%Y年%m月%d日 %H:%M")
    except Exception:
        return value


def send_webhook(payload):
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=30,
        )
    except requests.RequestException as error:
        print("Discord通信エラー:", error)
        return False

    print("Discord HTTPステータス:", response.status_code)

    if response.status_code == 204:
        return True

    print("Discordエラー内容:", response.text[:500])
    return False


def build_description(published, post_url, body):
    parts = []

    if published:
        parts.append("投稿日時: " + published)

    if post_url:
        parts.append("リンク: " + post_url)

    if body:
        parts.append(body)

    return "

".join(parts)


def main():
    print("=== GitHub Actions Instagram RSSテスト開始 ===")

    if not WEBHOOK_URL:
        print("WEBHOOK_TEST_TENが設定されていません")
        raise SystemExit(1)

    try:
        response = requests.get(
            FEED_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
    except requests.RequestException as error:
        print("RSS-Bridge通信エラー:", error)
        raise SystemExit(1)

    print("RSS-Bridge HTTPステータス:", response.status_code)

    if response.status_code != 200:
        print(response.text[:500])
        raise SystemExit(1)

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as error:
        print("Atom XML解析エラー:", error)
        raise SystemExit(1)

    entries = root.findall("atom:entry", NS)

    print("取得した投稿数:", len(entries))

    if not entries:
        print("投稿がありません")
        raise SystemExit(1)

    entry = entries[0]

    title = get_text(entry, "title")
    published_raw = get_text(entry, "published")
    published = format_time(published_raw)
    post_url = get_post_url(entry)
    image_urls = get_images(entry)

    summary = get_text(entry, "summary")
    content = get_text(entry, "content")

    body = summary or content

    print("タイトル:", title)
    print("投稿日時:", published)
    print("投稿URL:", post_url)
    print("画像枚数:", len(image_urls))
    print("投稿本文:", body if body else "(本文なし)")

    first_description = build_description(
        published,
        post_url,
        body,
    )

    first_payload = {
        "username": "GitHub Actions Instagramテスト",
        "embeds": [
            {
                "title": title[:256],
                "url": post_url,
                "description": first_description[:4096],
                "color": 15893389,
            }
        ],
    }

    print("本文メッセージを送信します")

    if not send_webhook(first_payload):
        raise SystemExit(1)

    for index, image_url in enumerate(image_urls, start=1):
        image_payload = {
            "username": "GitHub Actions Instagramテスト",
            "content": (
                "画像 "
                + str(index)
                + "/"
                + str(len(image_urls))
            ),
            "embeds": [
                {
                    "url": post_url,
                    "image": {
                        "url": image_url,
                    },
                    "color": 15893389,
                }
            ],
        }

        print(
            "画像メッセージを送信します:",
            str(index) + "/" + str(len(image_urls)),
        )

        if not send_webhook(image_payload):
            raise SystemExit(1)

    print("Discord通知に成功しました")
    print("=== GitHub Actions Instagram RSSテスト終了 ===")


if __name__ == "__main__":
    main()
