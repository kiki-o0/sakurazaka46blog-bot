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

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


MEMBERS = [
    {
        "username": "yamasaki.ten",
        "webhook_env": "WEBHOOK_TEN",
    },
    {
        "username": "airi.taniguchi.official",
        "webhook_env": "WEBHOOK_AIRI",
    },
    {
        "username": "rina_ino_",
        "webhook_env": "WEBHOOK_RINA_I",
    },
    {
        "username": "endohikari_official",
        "webhook_env": "WEBHOOK_HIKARI",
    },
    {
        "username": "ozonoreis2",
        "webhook_env": "WEBHOOK_REI",
    },
    {
        "username": "akiho_onuma_official",
        "webhook_env": "WEBHOOK_AKIHO",
    },
    {
        "username": "seki_yumiko_official",
        "webhook_env": "WEBHOOK_YUMIKO",
    },
    {
        "username": "takemotoyui_official",
        "webhook_env": "WEBHOOK_YUI",
    },
    {
        "username": "tamura.hono.official",
        "webhook_env": "WEBHOOK_HONO",
    },
    {
        "username": "fujiyoshi.karin",
        "webhook_env": "WEBHOOK_KARIN",
    },
    {
        "username": "matsudarina_official",
        "webhook_env": "WEBHOOK_RINA_M",
    },
    {
        "username": "rena_moriya_official",
        "webhook_env": "WEBHOOK_RENA",
    },
    {
        "username": "rika.ishimori.official",
        "webhook_env": "WEBHOOK_RIKA",
    },
    {
        "username": "riko.endo_official",
        "webhook_env": "WEBHOOK_RIKO",
    },
    {
        "username": "reinaodakura_official",
        "webhook_env": "WEBHOOK_REINA_O",
    },
    {
        "username": "yuzuki_nakashima_official",
        "webhook_env": "WEBHOOK_YUZUKI",
    },
    {
        "username": "yu.murai_official",
        "webhook_env": "WEBHOOK_YU",
    },
    {
        "username": "miumurayama_official",
        "webhook_env": "WEBHOOK_MIU",
    },
    {
        "username": "miichan_official",
        "webhook_env": "WEBHOOK_MINAMI",
    },
    {
        "username": "yuuka_sugai_official",
        "webhook_env": "WEBHOOK_YUUKA",
    },
]


def make_empty_history():
    return {
        member["username"]: []
        for member in MEMBERS
    }


def load_history():
    empty = make_empty_history()

    if not os.path.exists(HISTORY_FILE):
        print("履歴ファイルがありません")
        print("初回実行として処理します")
        return empty, True

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            old_history = json.load(file)
    except Exception as error:
        print("履歴ファイルの読み込みに失敗:", error)
        print("空の履歴として処理します")
        return empty, True

    history = {}
    needs_migration = False

    for member in MEMBERS:
        username = member["username"]
        value = old_history.get(username, [])

        if isinstance(value, list):
            history[username] = [
                str(item)
                for item in value
                if item
            ]
        else:
            history[username] = []
            needs_migration = True

    if set(old_history.keys()) != set(history.keys()):
        needs_migration = True

    return history, needs_migration


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


def format_cookie(value):
    value = value.strip()

    if not value:
        return ""

    if "=" in value:
        return value

    return "sessionid=" + value


def get_headers():
    raw_cookie = os.environ.get("INSTA_COOKIE", "")
    cookie = format_cookie(raw_cookie)

    headers = {
        "X-IG-App-ID": INSTAGRAM_APP_ID,
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
    }

    if cookie:
        headers["Cookie"] = cookie

    return headers


def fetch_user(username):
    url = (
        "https://www.instagram.com/api/v1/users/"
        "web_profile_info/"
    )

    try:
        response = ig_requests.get(
            url,
            params={"username": username},
            headers=get_headers(),
            impersonate="chrome",
            timeout=30,
        )
    except Exception as error:
        print("Instagram接続エラー:", error)
        return None

    print("HTTPステータス:", response.status_code)

    if response.status_code != 200:
        print(response.text[:300])
        return None

    try:
        data = response.json()
    except ValueError:
        print("JSONの解析に失敗しました")
        return None

    user = data.get("data", {}).get("user", {})

    if not user:
        print("ユーザー情報がありません")
        return None

    return user


def get_caption(node):
    edges = (
        node
        .get("edge_media_to_caption", {})
        .get("edges", [])
    )

    if not edges:
        return ""

    caption_node = edges[0].get("node", {})
    return caption_node.get("text", "")


def clean_caption(value):
    if not value:
        return ""

    value = html.unescape(value)
    value = re.sub(r"<[^>]*>", " ", value)
    value = re.sub(r"s+", " ", value)

    return value.strip()


def get_image_url(node):
    display_url = node.get("display_url", "")

    if display_url:
        return display_url

    image_versions = node.get("image_versions2", {})
    candidates = image_versions.get("candidates", [])

    if candidates:
        return candidates[0].get("url", "")

    return ""


def get_images(node):
    images = []

    sidecar = node.get(
        "edge_sidecar_to_children",
        {},
    )

    edges = sidecar.get("edges", [])

    for edge in edges:
        child = edge.get("node", {})
        image_url = get_image_url(child)

        if image_url and image_url not in images:
            images.append(image_url)

    if not images:
        image_url = get_image_url(node)

        if image_url:
            images.append(image_url)

    return images


def make_post(node):
    shortcode = node.get("shortcode", "")
    media_id = node.get("id", "")
    timestamp = node.get(
        "taken_at_timestamp",
        0,
    )

    post_id = shortcode or str(media_id)

    if shortcode:
        post_url = (
            "https://www.instagram.com/p/"
            + shortcode
            + "/"
        )
    else:
        post_url = ""

    try:
        timestamp = int(timestamp)
    except (TypeError, ValueError):
        timestamp = 0

    if timestamp:
        post_date = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        ).astimezone().strftime(
            "%Y年%m月%d日 %H:%M"
        )
    else:
        post_date = "日時不明"

    return {
        "id": post_id,
        "url": post_url,
        "date": post_date,
        "timestamp": timestamp,
        "caption": clean_caption(
            get_caption(node)
        ),
        "images": get_images(node),
    }


def get_recent_posts(user):
    edges = (
        user
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
        key=lambda post: post["timestamp"]
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
        print("Discord接続エラー:", error)
        return False

    print("Discord HTTPステータス:", response.status_code)

    if response.status_code in (200, 204):
        return True

    print("Discordエラー:", response.text[:500])
    return False


def send_post(username, webhook_url, post):
    description = (
        "投稿日時: "
        + post["date"]
        + "
リンク: "
        + post["url"]
    )

    if post["caption"]:
        description = (
            description
            + "

"
            + post["caption"]
        )

    first_payload = {
        "username": "Instagram通知",
        "embeds": [
            {
                "title": username,
                "url": post["url"],
                "description": description[:4096],
                "color": 15893389,
            }
        ],
    }

    print("本文メッセージを送信:", username)

    if not send_webhook(
        webhook_url,
        first_payload,
    ):
        return False

    time.sleep(DISCORD_INTERVAL_SECONDS)

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

        if not send_webhook(
            webhook_url,
            image_payload,
        ):
            return False

        time.sleep(DISCORD_INTERVAL_SECONDS)

    return True


def process_member(
    member,
    history,
    first_run,
):
    username = member["username"]
    webhook_env = member["webhook_env"]
    webhook_url = os.environ.get(
        webhook_env,
        "",
    ).strip()

    print()
    print("========================================")
    print("確認対象:", "@" + username)
    print("Webhook:", webhook_env)

    user = fetch_user(username)

    if user is None:
        print("取得失敗:", username)
        return False

    posts = get_recent_posts(user)

    if not posts:
        print("投稿なし:", username)
        return True

    print("取得投稿数:", len(posts))

    known_ids = set(
        history.get(username, [])
    )

    if first_run:
        print("初回のため通知せず履歴だけ作成")

        for post in posts:
            if post["id"] not in known_ids:
                history.setdefault(
                    username,
                    [],
                ).append(post["id"])

        return True

    new_posts = [
        post
        for post in posts
        if post["id"] not in known_ids
    ]

    if not new_posts:
        print("新着なし:", username)
        return True

    if not webhook_url:
        print("Webhook未設定:", webhook_env)
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

        history.setdefault(
            username,
            [],
        ).append(post["id"])

    return True


def main():
    print("=== Instagram全員分チェック開始 ===")

    if not os.environ.get(
        "INSTA_COOKIE",
        "",
    ).strip():
        print("警告: INSTA_COOKIEが未設定です")

    history, needs_migration = load_history()

    first_run = needs_migration

    if first_run:
        print("初回または履歴形式変更です")
        print("今回は通知せず、履歴だけ作成します")
    else:
        print("既存履歴と比較して新着を通知します")

    original = json.dumps(
        history,
        ensure_ascii=False,
        sort_keys=True,
    )

    all_success = True

    for member in MEMBERS:
        success = process_member(
            member,
            history,
            first_run,
        )

        if not success:
            all_success = False

        time.sleep(REQUEST_INTERVAL_SECONDS)

    updated = json.dumps(
        history,
        ensure_ascii=False,
        sort_keys=True,
    )

    if first_run or original != updated:
        save_history(history)
    else:
        print("履歴の変更はありません")

    print()
    print("=== Instagram全員分チェック終了 ===")

    if not all_success:
        print("一部のメンバーで失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
