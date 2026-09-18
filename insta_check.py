import json
import os
import sys
from curl_cffi import requests as ig_requests


INSTAGRAM_ID = "yamasaki.ten"
INSTAGRAM_APP_ID = "936619743392459"


def format_cookie(raw_cookie):
    raw_cookie = raw_cookie.strip()

    if not raw_cookie:
        return ""

    if "=" in raw_cookie:
        return raw_cookie

    return f"sessionid={raw_cookie}"


def main():
    print("=== Instagram取得テスト開始 ===")
    print(f"確認対象: @{INSTAGRAM_ID}")

    raw_cookie = os.environ.get("INSTA_COOKIE", "")

    if not raw_cookie:
        print("❌ INSTA_COOKIEが設定されていません")
        print("GitHub Secretsの名前がINSTA_COOKIEになっているか確認してください")
        sys.exit(1)

    cookie = format_cookie(raw_cookie)

    headers = {
        "X-IG-App-ID": INSTAGRAM_APP_ID,
        "Cookie": cookie,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }

    url = (
        "https://www.instagram.com/api/v1/users/"
        f"web_profile_info/?username={INSTAGRAM_ID}"
    )

    print("Instagramへ接続しています...")

    try:
        response = ig_requests.get(
            url,
            headers=headers,
            impersonate="chrome",
            timeout=20,
        )
    except Exception as error:
        print("❌ Instagramへの接続でエラーが発生しました")
        print(f"エラー内容: {error}")
        sys.exit(1)

    print(f"HTTPステータス: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', '')}")
    print(f"レスポンスサイズ: {len(response.content)} bytes")

    retry_after = response.headers.get("retry-after")
    if retry_after:
        print(f"Retry-After: {retry_after}")

    if response.status_code != 200:
        print("❌ Instagramから正常なHTTP 200が返りませんでした")
        print("レスポンス先頭200文字:")
        print(response.text[:200])
        sys.exit(1)

    try:
        data = response.json()
    except ValueError:
        print("❌ レスポンスがJSONではありません")
        print("レスポンス先頭200文字:")
        print(response.text[:200])
        sys.exit(1)

    user_data = data.get("data", {}).get("user", {})

    if not user_data:
        print("❌ JSON内にユーザー情報がありません")
        print("JSONの最上位キー:")
        print(list(data.keys()))
        sys.exit(1)

    media_edges = (
        user_data
        .get("edge_owner_to_timeline_media", {})
        .get("edges", [])
    )

    if not media_edges:
        print("⚠️ ユーザー情報は取得できましたが、投稿情報がありません")
        sys.exit(0)

    print(f"✅ 投稿情報を取得できました: {len(media_edges)}件")
    print()
    print("=== 取得した投稿 ===")

    for number, edge in enumerate(media_edges[:5], start=1):
        node = edge.get("node", {})
        shortcode = node.get("shortcode", "")
        taken_at = node.get("taken_at_timestamp", 0)
        post_url = f"https://www.instagram.com/p/{shortcode}/"

        caption = ""
        caption_edges = (
            node
            .get("edge_media_to_caption", {})
            .get("edges", [])
        )

        if caption_edges:
            caption = caption_edges[0].get("node", {}).get("text", "")

        print(f"{number}. {post_url}")
        print(f"   投稿日時: {taken_at}")
        print(f"   キャプション: {caption[:100]}")
        print()

    print("=== Instagram取得テスト終了 ===")


if __name__ == "__main__":
    main()
