import os
import json
import time
import random
from curl_cffi import requests as ig_requests
import requests

# ── メンバーリスト（IDは1文字ずつ事実確認済み）──────────────────────────
MEMBERS = [
    {"name": "山﨑天", "insta_id": "yamasaki.ten", "webhook_env": "WEBHOOK_TEN"},
    {"name": "谷口愛季", "insta_id": "airi.taniguchi.official", "webhook_env": "WEBHOOK_AIRI"},
    {"name": "井上梨名", "insta_id": "rina_ino_", "webhook_env": "WEBHOOK_RINA_I"},
    {"name": "遠藤光莉", "insta_id": "endohikari_official", "webhook_env": "WEBHOOK_HIKARI"},
    {"name": "大園玲", "insta_id": "ozonoreis2", "webhook_env": "WEBHOOK_REI"},
    {"name": "大沼晶保", "insta_id": "akiho_onuma_official", "webhook_env": "WEBHOOK_AKIHO"},
    {"name": "関有美子", "insta_id": "seki_yumiko_official", "webhook_env": "WEBHOOK_YUMIKO"},
    {"name": "武元唯衣", "insta_id": "takemotoyui_official", "webhook_env": "WEBHOOK_YUI"},
    {"name": "田村保乃", "insta_id": "tamura.hono.official", "webhook_env": "WEBHOOK_HONO"},
    {"name": "藤吉夏鈴", "insta_id": "fujiyoshi.karin", "webhook_env": "WEBHOOK_KARIN"},
    {"name": "松田里奈", "insta_id": "matsudarina_official", "webhook_env": "WEBHOOK_RINA_M"},
    {"name": "守屋麗奈", "insta_id": "rena_moriya_official", "webhook_env": "WEBHOOK_RENA"},
    {"name": "石森璃花", "insta_id": "rika.ishimori.official", "webhook_env": "WEBHOOK_RIKA"},
    {"name": "遠藤理子", "insta_id": "riko.endo_official", "webhook_env": "WEBHOOK_RIKO"},
    {"name": "小田倉麗奈", "insta_id": "reinaodakura_official", "webhook_env": "WEBHOOK_REINA_O"},
    {"name": "中嶋優月", "insta_id": "yuzuki_nakashima_official", "webhook_env": "WEBHOOK_YUZUKI"},
    {"name": "村井優", "insta_id": "yu.murai_official", "webhook_env": "WEBHOOK_YU"},
    {"name": "村山美羽", "insta_id": "miumurayama_official", "webhook_env": "WEBHOOK_MIU"},
    {"name": "小池美波", "insta_id": "miichan_official", "webhook_env": "WEBHOOK_MINAMI"},
    {"name": "菅井友香", "insta_id": "yuuka_sugai_official", "webhook_env": "WEBHOOK_YUUKA"},
]

HISTORY_FILE = "insta_history.json"
IG_APP_ID = "936619743392459"
MAX_POSTS_TO_CHECK = 5


def format_cookie(raw_cookie):
    """
    INSTA_COOKIE環境変数の値を整形する。
    ・「sessionid=abc123; csrftoken=xxx; ...」のようなCookie全文
    ・「abc123」のようなsessionid値だけ
    どちらでも動くようにする。
    """
    raw = raw_cookie.strip()
    if not raw:
        return ""
    if "=" in raw:
        return raw
    return f"sessionid={raw}"


def get_recent_posts(insta_id, cookie_str):
    """
    Instagram内部API（web_profile_info）を使って最新投稿リストを取得する。
    curl_cffiでChromeのTLSフィンガープリントを偽装し、ブロックを回避する。
    ピン留め投稿の影響を避けるため、取得後に taken_at_timestamp でソートする。
    """
    headers = {
        "X-IG-App-ID": IG_APP_ID,
        "Cookie": cookie_str,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }

    # エンドポイントのフォールバック：
    # i.instagram.com がダメなら www.instagram.com を試す
    api_urls = [
        f"https://i.instagram.com/api/v1/users/web_profile_info?username={insta_id}",
        f"https://www.instagram.com/api/v1/users/web_profile_info/?username={insta_id}",
    ]

    for api_url in api_urls:
        try:
            response = ig_requests.get(
                api_url,
                headers=headers,
                impersonate="chrome",
                timeout=15,
            )

            if response.status_code != 200:
                continue

            data = response.json()
            user_data = data.get("data", {}).get("user", {})
            if not user_data:
                continue

            media_edges = (
                user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])
            )
            if not media_edges:
                return []

            posts = []
            for edge in media_edges[:MAX_POSTS_TO_CHECK]:
                node = edge.get("node", {})
                if not node:
                    continue

                caption = ""
                caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                if caption_edges:
                    caption = caption_edges[0]["node"]["text"]

                shortcode = node.get("shortcode", "")
                if not shortcode:
                    continue

                posts.append({
                    "shortcode": shortcode,
                    "url": f"https://www.instagram.com/p/{shortcode}/",
                    "caption": caption,
                    "image_url": node.get("display_url", ""),
                    "is_video": node.get("is_video", False),
                    "taken_at": node.get("taken_at_timestamp", 0),
                })

            # ピン留め投稿がedges[0]に来る場合があるので、
            # taken_at（投稿日時）の降順でソートして本当の最新を先頭にする
            posts.sort(key=lambda p: p["taken_at"], reverse=True)

            return posts

        except Exception as e:
            print(f"  ⚠ エラー（{api_url.split('/')[2]}）: {e}")
            continue

    print(f"  ⚠ 全てのエンドポイントで取得に失敗しました（Cookie期限切れの可能性）")
    return []


def send_discord_notification(webhook_url, member_name, post):
    """
    Discord WebhookにEmbed形式で通知を送信する。
    投稿URL・キャプション・画像を含めてリッチに表示。
    """
    embed = {
        "title": f"📷 {member_name}のInstagramが更新されました！",
        "url": post["url"],
        "color": 15893389,
        "description": post["caption"][:2000] if post["caption"] else "（キャプションなし）",
        "footer": {"text": "Instagram"},
    }

    if post.get("image_url"):
        embed["image"] = {"url": post["image_url"]}

    payload = {
        "username": f"{member_name} Instagram",
        "embeds": [embed],
    }

    try:
        requests.post(webhook_url, json=payload, timeout=15)
        print(f"  ✅ Discord通知を送信しました: {post['url']}")
    except Exception as e:
        print(f"  ⚠ Discord送信エラー: {e}")


def main():
    print("=== Instagram確認スタート ===")

    raw_cookie = os.environ.get("INSTA_COOKIE")
    if not raw_cookie:
        print("❌ INSTA_COOKIE環境変数が設定されていません")
        print("   GitHub Secrets に INSTA_COOKIE を追加してください")
        return

    cookie_str = format_cookie(raw_cookie)

    # ── 履歴ファイルを読み込む ────────────────────────────────────────
    # 履歴の形式: { "insta_id": [shortcode1, shortcode2, ...], ... }
    # ※旧形式（insta_id: "caption文字列"）との互換性も考慮
    history = {}
    is_first_run = True
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                raw_history = json.load(f)
            for key, val in raw_history.items():
                if isinstance(val, list):
                    history[key] = val
                elif isinstance(val, str):
                    # 旧形式（caption文字列）→ 空リストにして初回通知をスキップ
                    history[key] = []
                else:
                    history[key] = []
            if any(isinstance(v, list) and len(v) > 0 for v in raw_history.values()):
                is_first_run = False
        except Exception:
            pass

    is_updated = False

    for member in MEMBERS:
        webhook_url = os.environ.get(member["webhook_env"])
        if not webhook_url:
            continue

        print(f"👀 {member['name']} ({member['insta_id']}) を確認中...")

        posts = get_recent_posts(member["insta_id"], cookie_str)
        if not posts:
            time.sleep(random.uniform(2, 4))
            continue

        known_shortcodes = set(history.get(member["insta_id"], []))

        # 未通知の投稿を抽出（古い順に通知するため逆順で処理）
        new_posts = [p for p in posts if p["shortcode"] not in known_shortcodes]

        if new_posts:
            new_posts.reverse()

            for post in new_posts:
                if is_first_run:
                    print(f"  📌 初回実行: {member['name']} の投稿を履歴に記録（通知スキップ）: {post['url']}")
                else:
                    print(f"✨ {member['name']} の新しい投稿を発見！")
                    send_discord_notification(webhook_url, member["name"], post)

            all_shortcodes = [p["shortcode"] for p in posts] + list(known_shortcodes)
            seen = set()
            unique_shortcodes = []
            for sc in all_shortcodes:
                if sc not in seen:
                    seen.add(sc)
                    unique_shortcodes.append(sc)
            history[member["insta_id"]] = unique_shortcodes[:50]
            is_updated = True
        else:
            print(f"➡️ {member['name']} は更新なし")

        time.sleep(random.uniform(2, 5))

    if is_updated:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print("💾 履歴を保存しました")

    print("=== 確認終了 ===")


if __name__ == "__main__":
    main()
