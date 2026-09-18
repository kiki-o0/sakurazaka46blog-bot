import html
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

from curl_cffi import requests as ig_requests
import requests


INSTAGRAM_APP_ID = "936619743392459"
HISTORY_FILE = "insta_history.json"

MAX_POSTS_TO_CHECK = 5
REQUEST_INTERVAL_SECONDS = 3
DISCORD_INTERVAL_SECONDS = 1

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


MEMBERS = [
    {
        "username": "yamasaki.ten",
        "webhook_env": "WEBHOOK_YAMASAKI",
    },
    {
        "username": "airi.taniguchi.official",
        "webhook_env": "WEBHOOK_TANIGUCHI",
    },
    {
        "username": "rina_ino_",
        "webhook_env": "WEBHOOK_INO",
    },
    {
        "username": "endohikari_official",
        "webhook_env": "WEBHOOK_ENDO_H",
    },
    {
        "username": "ozonoreis2",
        "webhook_env": "WEBHOOK_OZONO",
    },
    {
        "username": "akiho_onuma_official",
        "webhook_env": "WEBHOOK_ONUMA",
    },
    {
        "username": "seki_yumiko_official",
        "webhook_env": "WEBHOOK_SEKI",
    },
    {
        "username": "takemotoyui_official",
        "webhook_env": "WEBHOOK_TAKEMOTO",
    },
    {
        "username": "tamura.hono.official",
        "webhook_env": "WEBHOOK_TAMURA",
    },
    {
        "username": "fujiyoshi.karin",
        "webhook_env": "WEBHOOK_FUJIYOSHI",
    },
    {
        "username": "matsudarina_official",
        "webhook_env": "WEBHOOK_MATSUDA",
    },
    {
        "username": "rena_moriya_official",
        "webhook_env": "WEBHOOK_MORIYA",
    },
    {
        "username": "rika.ishimori.official",
        "webhook_env": "WEBHOOK_ISHIMORI",
    },
    {
        "username": "riko.endo_official",
        "webhook_env": "WEBHOOK_ENDO_R",
    },
    {
        "username": "reinaodakura_official",
        "webhook_env": "WEBHOOK_ODAKURA",
    },
    {
        "username": "yuzuki_nakashima_official",
        "webhook_env": "WEBHOOK_NAKASHIMA",
    },
    {
        "username": "yu.murai_official",
        "webhook_env": "WEBHOOK_MURAI",
    },
    {
        "username": "miumurayama_official",
        "webhook_env": "WEBHOOK_MURAYAMA",
    },
    {
        "username": "miichan_official",
        "webhook_env": "WEBHOOK_MIICHAN",
    },
    {
        "username": "yuuka_sugai_official",
        "webhook_env": "WEBHOOK_SUGAI",
    },
]


def empty_history():
    return {
        member["username"]: []
        for member in MEMBERS
    }


def load_history():
    if not os.path.exists(HISTORY_FILE):
        print("履歴ファイルがありません。新規作成します")
        return empty_history(), True

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            loaded = json.load(file)
    except Exception as error:
        print("履歴ファイルを読み込めません:", error)
        print("空の履歴として開始します")
        return empty_history(), True

    migrated = False
    history = {}

    for member in MEMBERS:
        username = member["username"]
        value = loaded.get(username, [])

        if isinstance(value, list):
            history[username] = [
                str(item)
                for item in value
                if item
            ]
        else:
            history[username] = []
            migrated = True

    if set(loaded.keys()) != set(history.keys()):
        migrated = True

    return history, migrated


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("履歴ファイルを保存しました:", HISTORY_FILE)


def format_cookie(raw_cookie):
    raw_cookie = raw_cookie.strip()

    if not raw_cookie:
        return ""

    if "=" in raw_cookie:
        return raw_cookie

    return "sessionid=" + raw_cookie


def get_instagram_headers():
    raw_cookie = os.environ.get("INSTA_COOKIE", "")
    cookie = format_cookie(raw_cookie)

    headers = {
        "X-IG-App-ID": INSTAGRAM_APP_ID,
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "*/*",
    }

    if cookie:
        headers["Cookie"] = cookie

    return headers


def fetch_profile(username):
    url = (
        "https://www.instagram.com/api/v1/users/"
        "web_profile_info/"
    )

    params = {
        "username": username,
    }

    try:
        response = ig_requests.get(
            url,
            params=params,
            headers=get_instagram_headers(),
            impersonate="chrome",
            timeout=30,
        )
    except Exception as error:
        print("Instagram接続エラー:", error)
        return None

    print("Instagram HTTPステータス:", response.status_code)

    if response.status_code != 200:
        print("レスポンス先頭:", response.text[:200])
        return None

    try:
        data = response.json()
    except ValueError:
        print("InstagramレスポンスがJSONではありません")
        return None

    user_data = data.get("data", {}).get("user", {})

    if not user_data:
        print("ユーザー情報がありません")
        return None

    return user_data


def get_caption(node):
    caption_edges = (
        node
        .get("edge_media_to_caption", {})
        .get("edges", [])
    )

    if not caption_edges:
        return ""

    caption_node = caption_edges[0].get("node", {})
    return caption_node.get("text", "")


def get_image_url(node):
    display_url = node.get("display_url", "")

    if display_url:
        return display_url

    image_versions = node.get("image_versions2", {})
    candidates = image_versions.get("candidates", [])

    if candidates:
        return candidates[0].get("url", "")

    return ""


def get_node_images(node):
    images = []

    carousel = node.get("edge_sidecar_to_children", {})
    carousel_edges = carousel.get("edges", [])

    if carousel_edges:
        for child_edge in carousel_edges:
            child = child_edge.get("node", {})
            image_url = get_image_url(child)

            if image_url and image_url not in images:
                images.append(image_url)

    if not images:
        image_url = get_image_url(node)

        if image_url:
            images.append(image_url)

    return images


def get_post_url(node):
    shortcode = node.get("shortcode", "")

    if not shortcode:
        return ""

    return "https://www.instagram.com/p/" + shortcode + "/"


def get_post_id(node):
    shortcode = node.get("shortcode", "")

    if shortcode:
        return shortcode

    media_id = node.get("id", "")

    if media_id:
        return str(media_id)

    return ""


def get_post_timestamp(node):
    value = node.get("taken_at_timestamp", 0)

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def format_post_time(timestamp):
    if not timestamp:
        return "日時不明"

    try:
        value = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )

        return value.astimezone().strftime(
            "%Y年%m月%d日 %H:%M"
        )
    except Exception:
        return "日時不明"


def clean_caption(value):
    if not value:
        return ""

    value = html.unescape(value)
    value = re.sub(r"<[^>]*>", " ", value)
    value = re.sub(r"s+", " ", value)

    return value.strip()


def make_post(node):
    post_id = get_post_id(node)
    post_url = get_post_url(node)
    timestamp = get_post_timestamp(node)
    caption = clean_caption(get_caption(node))
    images = get_node_images(node)

    return {
        "id": post_id,
        "url": post_url,
        "timestamp": timestamp,
        "date": format_post_time(timestamp),
        "caption": caption,
        "images": images,
    }


def get_recent_posts(user_data):
    edges = (
        user_data
        .get("edge_owner_to_timeline_media", {})
        .get("edges", [])
    )

    posts = []

    for edge in edges[:MAX_POSTS_TO_CHECK]:
        node = edge.get("node", {})
        post = make_post(node)

        if post["id"]:
            posts.append(post)

    posts.sort(
        key=lambda item: item["timestamp"]
    )

    return posts


def send_webhook(webhook_url, payload):
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=30,
        )
    except requests.RequestException as error:
        print("Discord通信エラー:", error)
        return False

    print("Discord HTTPステータス:", response.status_code)

    if response.status_code in (200, 204):
        return True

    print("Discordエラー内容:", response.text[:500])
    return False


def send_post(webhook_url, username, post):
    caption = post["caption"]

    description = (
        "投稿日時: "
        + post["date"]
        + "
リンク: "
        + post["url"]
    )

    if caption:
        description = description + "

" + caption

    first_payload = {
        "username": "Instagram通知 - " + username,
        "embeds": [
            {
                "title": username,
                "url": post["url"],
                "description": description[:4096],
                "color": 15893389,
            }
        ],
    }

    print("本文メッセージを送信します")

    if not send_webhook(webhook_url, first_payload):
        return False

    time.sleep(DISCORD_INTERVAL_SECONDS)

    total = len(post["images"])

    for index, image_url in enumerate(post["images"], start=1):
        image_payload = {
            "username": "Instagram通知 - " + username,
            "content": (
                username
                + " 画像 "
                + str(index)
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
            str(index) + "/" + str(total),
        )

        if not send_webhook(webhook_url, image_payload):
            return False

        time.sleep(DISCORD_INTERVAL_SECONDS)

    return True


def process_member(member, history, first_run):
    username = member["username"]
    webhook_env = member["webhook_env"]
    webhook_url = os.environ.get(webhook_env, "").strip()

    print()
    print("========================================")
    print("確認対象:", "@" + username)
    print("Webhook環境変数:", webhook_env)

    user_data = fetch_profile(username)

    if user_data is None:
        print("取得失敗:", username)
        return False

    posts = get_recent_posts(user_data)

    if not posts:
        print("投稿がありません:", username)
        return True

    print("取得投稿数:", len(posts))

    known_ids = set(history.get(username, []))

    if first_run:
        print("初回実行のため、通知せず履歴だけ作成します")

        for post in posts:
            if post["id"] not in known_ids:
                history.setdefault(username, []).append(
                    post["id"]
                )

        return True

    new_posts = [
        post
        for post in posts
        if post["id"] not in known_ids
    ]

    if not new_posts:
        print("新着投稿なし:", username)
        return True

    if not webhook_url:
        print("Webhook未設定のため送信できません")
        print("環境変数:", webhook_env)
        return False

    for post in new_posts:
        print("新着投稿:", post["url"])
        print("画像枚数:", len(post["images"]))

        success = send_post(
            webhook_url,
            username,
            post,
        )

        if not success:
            print("通知失敗。履歴には追加しません")
            return False

        history.setdefault(username, []).append(
            post["id"]
        )

    return True


def main():
    print("=== Instagram全員分チェック開始 ===")

    if not os.environ.get("INSTA_COOKIE", "").strip():
        print("警告: INSTA_COOKIEが設定されていません")

    history, history_needs_migration = load_history()

    first_run = history_needs_migration

    if first_run:
        print("初回または履歴形式変更を検出しました")
        print("今回の実行では通知せず、履歴だけ作成します")
    else:
        print("既存履歴を使用して新着投稿を確認します")

    all_success = True
    history_changed = False

    before_history = json.dumps(
        history,
        ensure_ascii=False,
        sort_keys=True,
    )

    for member in MEMBERS:
        success = process_member(
            member,
            history,
            first_run,
        )

        if not success:
            all_success = False

        time.sleep(REQUEST_INTERVAL_SECONDS)

    after_history = json.dumps(
        history,
        ensure_ascii=False,
        sort_keys=True,
    )

    if before_history != after_history:
        history_changed = True

    if history_changed or first_run:
        save_history(history)
    else:
        print("履歴に変更はありません")

    print()
    print("=== Instagram全員分チェック終了 ===")

    if not all_success:
        print("一部メンバーの処理に失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
