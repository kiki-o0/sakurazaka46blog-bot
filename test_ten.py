import html
import xml.etree.ElementTree as ET
import os
from datetime import datetime

import requests


FEED_URL = "https://rss-bridge.org/bridge01/?action=display&bridge=InstagramBridge&context=Username&u=yamasaki.ten&media_type=all&format=Atom"
WEBHOOK_URL = os.environ.get("WEBHOOK_TEST_TEN", "").strip()

NS = {
    "atom": "http://www.w3.org/2005/Atom",
}


def get_text(parent, name):
    node = parent.find("atom:" + name, NS)

    if node is None or node.text is None:
        return ""

    return html.unescape(node.text).strip()


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

    return images[:9]


def format_time(value):
    try:
        date_value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return date_value.astimezone().strftime("%Y年%m月%d日 %H:%M")
    except Exception:
        return value


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
        print("Atom解析エラー:", error)
        raise SystemExit(1)

    entries = root.findall("atom:entry", NS)
    print("取得した投稿数:", len(entries))

    if not entries:
        print("投稿がありません")
        raise SystemExit(1)

    entry = entries[0]

    title = get_text(entry, "title")
    published = get_text(entry, "published")
    post_url = get_post_url(entry)
    image_urls = get_images(entry)

    print("タイトル:", title)
    print("投稿日時:", format_time(published))
    print("投稿URL:", post_url)
    print("画像枚数:", len(image_urls))

    description = "投稿日時 " + format_time(published)

    embeds = [
        {
            "title": title[:256],
            "url": post_url,
            "description": description,
            "color": 15893389,
        }
    ]

    for image_url in image_urls:
        embeds.append(
            {
                "url": post_url,
                "image": {
                    "url": image_url,
                },
                "color": 15893389,
            }
        )

    payload = {
        "username": "GitHub Actions Instagramテスト",
        "embeds": embeds,
    }

    try:
        discord_response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=30,
        )
    except requests.RequestException as error:
        print("Discord通信エラー:", error)
        raise SystemExit(1)

    print("Discord HTTPステータス:", discord_response.status_code)

    if discord_response.status_code != 204:
        print(discord_response.text[:500])
        raise SystemExit(1)

    print("Discord通知に成功しました")
    print("=== GitHub Actions Instagram RSSテスト終了 ===")


if __name__ == "__main__":
    main()
