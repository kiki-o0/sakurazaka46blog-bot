import os
import requests

webhook_url = os.environ.get("WEBHOOK_TEST_TEN")

profile_url = "https://www.instagram.com/yamasaki.ten/"
embed = {
    "title": "山﨑天のInstagramを確認",
    "url": profile_url,
    "description": (
        "Instagramの投稿ページを直接取得できない場合に備えた"
        "プロフィール誘導用のテスト通知です。

"
        "「プロフィールを開く」を押して最新投稿を確認できます。"
    ),
    "color": 15893389,
    "footer": {"text": "櫻坂通知ロボ・テスト環境"}
}

response = requests.post(
    webhook_url,
    json={
        "username": "山﨑天 Instagram",
        "embeds": [embed]
    },
    timeout=15
)

print(response.status_code)
response.raise_for_status()
