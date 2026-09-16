import os
import json
from datetime import datetime, timezone, timedelta
import requests

HISTORY_FILE = "test_ten_history.json"
WEBHOOK_URL = os.environ.get("WEBHOOK_TEST_TEN")

JST = timezone(timedelta(hours=9))
now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")

# 本番ではここが「Instagram側から得られた投稿ID」になる想定。
# まずは手で好きな文字列を変更して、通知の再現をテストする。
TEST_POST_ID = "test-post-001"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def send_notification():
    profile_url = "https://www.instagram.com/yamasaki.ten/"

    payload = {
        "username": "山﨑天 Instagram（テスト）",
        "embeds": [
            {
                "title": "🌸 山﨑天のInstagramを確認",
                "url": profile_url,
                "description": (
                    "テスト用の更新検知通知です。
"
                    "「投稿を確認する」ため、プロフィールを開いてください。"
                ),
                "color": 15893389,
                "fields": [
                    {
                        "name": "検知ID",
                        "value": TEST_POST_ID,
                        "inline": True
                    },
                    {
                        "name": "検知日時",
                        "value": now,
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "櫻坂通知ロボ・test_ten"
                }
            }
        ]
    }

    response = requests.post(WEBHOOK_URL, json=payload, timeout=15)
    response.raise_for_status()

def main():
    if not WEBHOOK_URL:
        raise RuntimeError("WEBHOOK_TEST_TEN がGitHub Secretsに設定されていません。")

    history = load_history()
    previous_id = history.get("latest_post_id")

    if previous_id == TEST_POST_ID:
        print("➡️ 前回と同じIDです。通知しません。")
        return

    send_notification()
    history["latest_post_id"] = TEST_POST_ID
    history["updated_at"] = now
    save_history(history)

    print("✨ テスト通知を送信し、履歴を更新しました。")

if __name__ == "__main__":
    main()
