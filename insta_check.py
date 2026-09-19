import html
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime


import requests


HISTORY_FILE = "insta_history.json"
WAIT_SECONDS = 5
DISCORD_WAIT_SECONDS = 1
ATOM_NS = "http://www.w3.org/2005/Atom"


RSS_URL = (
    "https://rss-bridge.org/bridge01/"
    "?action=display"
    "&bridge=InstagramBridge"
    "&context=Username"
    "&u={username}"
    "&media_type=all"
    "&format=Atom"
)


MEMBERS = [
    ("yamasaki.ten", "WEBHOOK_TEN"),
    ("airi.taniguchi.official", "WEBHOOK_AIRI"),
    ("rina_ino_", "WEBHOOK_RINA_I"),
    ("endohikari_official", "WEBHOOK_HIKARI"),
    ("ozonoreis2", "WEBHOOK_REI"),
    ("akiho_onuma_official", "WEBHOOK_AKIHO"),
    ("seki_yumiko_official", "WEBHOOK_YUMIKO"),
    ("takemotoyui_official", "WEBHOOK_YUI"),
    ("tamura.hono.official", "WEBHOOK_HONO"),
    ("fujiyoshi.karin", "WEBHOOK_KARIN"),
    ("matsudarina_official", "WEBHOOK_RINA_M"),
    ("rena_moriya_official", "WEBHOOK_RENA"),
    ("rika.ishimori.official", "WEBHOOK_RIKA"),
    ("riko.endo_official", "WEBHOOK_RIKO"),
    ("reinaodakura_official", "WEBHOOK_REINA_O"),
    ("yuzuki_nakashima_official", "WEBHOOK_YUZUKI"),
    ("yu.murai_official", "WEBHOOK_YU"),
    ("miumurayama_official", "WEBHOOK_MIU"),
    ("miichan_official", "WEBHOOK_MINAMI"),
    ("yuuka_sugai_official", "WEBHOOK_YUUKA"),
]


def make_empty_history():
    result = {}

    for username, webhook_name in MEMBERS:
        result[username] = []

    return result


def load_history():
    empty = make_empty_history()

    if not os.path.exists(HISTORY_FILE):
        print("履歴ファイルなし")
        return empty, True

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            old_data = json.load(file)
    except Exception as error:
        print("履歴読み込みエラー:", error)
        return empty, True

    history = {}
    migration = False

    for username, webhook_name in MEMBERS:
        value = old_data.get(username, [])

        if isinstance(value, list):
            history[username] = []

            for item in value:
                if item:
                    history[username].append(str(item))
        else:
            history[username] = []
            migration = True

    if set(old_data.keys()) != set(history.keys()):
        migration = True

    return history, migration


def save_history(history):
    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("履歴を保存しました")


def text_from_entry(entry, name):
    tag = "{" + ATOM_NS + "}" + name
    node = entry.find(tag)

    if node is None:
        return ""

    return "".join(node.itertext()).strip()


def entry_url(entry):
    link_tag = "{" + ATOM_NS + "}link"

    for node in entry.findall(link_tag):
        href = node.attrib.get("href", "")
        rel = node.attrib.get("rel", "")

        if href and rel == "alternate":
            return href

    for node in entry.findall(link_tag):
        href = node.attrib.get("href", "")

        if href:
            return href

    return ""


def entry_images(entry):
    images = []
    link_tag = "{" + ATOM_NS + "}link"

    for node in entry.findall(link_tag):
        href = node.attrib.get("href", "")
        rel = node.attrib.get("rel", "")
        link_type = node.attrib.get("type", "")

        if rel == "enclosure":
            if href and link_type.startswith("image/"):
                if href not in images:
                    images.append(href)

    return images


def clean_text(value):
    if not value:
        return ""

    value = html.unescape(value)
    value = value.replace("<br>", " ")
    value = value.replace("<br/>", " ")
    value = value.replace("<br />", " ")
    value = value.replace("<p>", " ")
    value = value.replace("</p>", " ")

    while "  " in value:
        value = value.replace("  ", " ")

    return value.strip()


def format_date(value):
    if not value:
        return ""

    try:
        converted = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        return converted.astimezone().strftime(
            "%Y年%m月%d日 %H:%M"
        )
    except Exception:
        return value


def read_feed(username):
    url = RSS_URL.format(
        username=username,
    )

    print("RSS取得:", username)

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
            },
            timeout=40,
        )
    except requests.RequestException as error:
        print("RSS接続エラー:", error)
        return None

    print("RSS HTTPステータス:", response.status_code)

    if response.status_code != 200:
        print(response.text[:300])
        return None

    try:
        return ET.fromstring(response.content)
    except ET.ParseError as error:
        print("XML解析エラー:", error)
        return None


def get_posts(root):
    entry_tag = "{" + ATOM_NS + "}entry"
    entries = root.findall(entry_tag)
    posts = []

    for entry in entries:
        title = text_from_entry(entry, "title")
        published = text_from_entry(entry, "published")
        updated = text_from_entry(entry, "updated")
        date_value = published or updated
        url = entry_url(entry)
        post_id = text_from_entry(entry, "id")

        summary = text_from_entry(entry, "summary")
        content = text_from_entry(entry, "content")
        body = summary or content

        posts.append(
            {
                "id": post_id or url,
                "title": title,
                "date": format_date(date_value),
                "url": url,
                "body": clean_text(body),
                "images": entry_images(entry),
            }
        )

    return posts


def send_discord(webhook_url, payload):
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=30,
        )
    except requests.RequestException as error:
        print("Discord接続エラー:", error)
        return False

    print("Discord HTTPステータス:", response.status_code)

    if response.status_code in (200, 204):
        return True

    print("Discordエラー:", response.text[:500])
    return False


def send_post(username, webhook_url, post):
    description = "投稿日時: " + post["date"]
    description = description + " / リンク: " + post["url"]

    if post["body"]:
        description = description + " / " + post["body"]

    payload = {
        "username": "Instagram通知",
        "embeds": [
            {
                "title": post["title"][:256],
                "url": post["url"],
                "description": description[:4096],
                "color": 15893389,
            }
        ],
    }

    print("本文送信:", username)

    if not send_discord(
        webhook_url,
        payload,
    ):
        return False

    time.sleep(DISCORD_WAIT_SECONDS)

    total = len(post["images"])

    for number, image_url in enumerate(
        post["images"],
        start=1,
    ):
        image_payload = {
            "username": "Instagram通知",
            "content": (
                username
                + " 画像 "
                + str(number)
                + "/"
                + str(total)
            ),
            "embeds": [
                {
                    "url": post["url"],
                    "image": {
                        "url": image_url,
                    },
                    "color": 15893389,
                }
            ],
        }

        print(
            "画像送信:",
            username,
            str(number) + "/" + str(total),
        )

        if not send_discord(
            webhook_url,
            image_payload,
        ):
            return False

        time.sleep(DISCORD_WAIT_SECONDS)

    return True


def process_member(
    username,
    webhook_name,
    history,
    first_run,
):
    print("========================================")
    print("確認対象:", "@" + username)
    print("Webhook:", webhook_name)

    root = read_feed(username)

    if root is None:
        print("RSS取得失敗:", username)
        return False

    posts = get_posts(root)

    print("取得投稿数:", len(posts))

    if not posts:
        print("投稿なし:", username)
        return True

    known = set(history.get(username, []))

    if first_run:
        print("初回のため通知せず履歴だけ作成")

        for post in posts:
            if post["id"] not in known:
                history[username].append(post["id"])

        return True

    new_posts = []

    for post in posts:
        if post["id"] not in known:
            new_posts.append(post)

    if not new_posts:
        print("新着なし:", username)
        return True

    webhook_url = os.environ.get(
        webhook_name,
        "",
    ).strip()

    if not webhook_url:
        print("Webhook未設定:", webhook_name)
        return False

    for post in new_posts:
        print("新着投稿:", post["url"])
        print("画像枚数:", len(post["images"]))

        success = send_post(
            username,
            webhook_url,
            post,
        )

        if not success:
            print("送信失敗。履歴には追加しません")
            return False

        history[username].append(post["id"])

    return True


def main():
    print("=== RSS-Bridge Instagram全員分チェック開始 ===")

    history, migration = load_history()
    first_run = migration

    if first_run:
        print("初回または履歴形式変更")
        print("通知せず履歴だけ作成します")
    else:
        print("履歴と比較して新着だけ通知します")

    before = json.dumps(
        history,
        ensure_ascii=False,
        sort_keys=True,
    )

    all_success = True

    for username, webhook_name in MEMBERS:
        result = process_member(
            username,
            webhook_name,
            history,
            first_run,
        )

        if not result:
            all_success = False

        time.sleep(WAIT_SECONDS)

    after = json.dumps(
        history,
        ensure_ascii=False,
        sort_keys=True,
    )

    if first_run or before != after:
        save_history(history)
    else:
        print("履歴変更なし")

    print("=== RSS-Bridge Instagram全員分チェック終了 ===")

    if not all_success:
        print("一部のメンバーで失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
