import html
import os
import xml.etree.ElementTree as ET
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

    return images


def format_time(value):
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

    print(response.text[:500])
    return False


def main():
    print("=== GitHub Actions Instagram RSSテスト開始 ===")

    if not WEBHOOK_URL:
        print("WEBHOOK_TEST_TENが設定されていません")
        raise SystemExit(1)

    response = requests.get(
        FEED_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )

    print("RSS-Bridge HTTPステータス:", response.status_code)

    if response.status_code != 200:
        print(response.text[:500])
        raise SystemExit(1)

    root = ET.fromstring(response.content)
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
    japan_time = format_time(published)

    print("タイトル:", title)
    print("投稿日時:", japan_time)
    print("投稿URL:", post_url)
    print("画像枚数:", len(image_urls))

    description = "投稿日時: " + japan_time + " / " + post_url

    text_payload = {
        "username": "GitHub Actions Instagramテスト",
        "embeds": [
            {
                "title": title[:256],
                "url": post_url,
                "description": description,
                "color": 15893389,
            }
        ],
    }

    print("本文メッセージを送信します")

    if not send_webhook(text_payload):
        raise SystemExit(1)

    for start in range(0, len(image_urls), 10):
        image_group = image_urls[start:start + 10]
        image_embeds = []

        for image_url in image_group:
            image_embeds.append(
                {
                    "url": post_url,
                    "image": {
                        "url": image_url,
                    },
                    "color": 15893389,
                }
            )

        range_text = (
            str(start + 1)
            + "〜"
            + str(start + len(image_group))
        )

        image_payload = {
            "username": "GitHub Actions Instagramテスト",
            "content": "画像 " + range_text + " / " + post_url,
            "embeds": image_embeds,
        }

        print("画像メッセージを送信します:", range_text)

        if not send_webhook(image_payload):
            raise SystemExit(1)

    print("Discord通知に成功しました")
    print("=== GitHub Actions Instagram RSSテスト終了 ===")


if __name__ == "__main__":
    main()
