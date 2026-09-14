import os
import re
import json
import requests
from bs4 import BeautifulSoup

# --- テスト用：メンバー2名の設定 ---
MEMBERS = [
    {"name": "山﨑天", "insta_id": "yamasaki.ten", "webhook_env": "WEBHOOK_TEN"},
    {"name": "谷口愛季", "insta_id": "airi.taniguchi.official", "webhook_env": "WEBHOOK_AIRI"},
]

HISTORY_FILE = "insta_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_latest_post(insta_id):
    url = f"https://www.picnob.com/profile/{insta_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        post_item = soup.select_one(".posts .post-item a")
        
        if not post_item:
            return None

        post_link = post_item.get("href", "")
        shortcode_match = re.search(r'/post/([^/]+)/', post_link)
        if not shortcode_match:
            return None

        shortcode = shortcode_match.group(1)
        actual_insta_url = f"https://www.instagram.com/p/{shortcode}/"

        img_tag = post_item.select_one("img")
        img_url = img_tag.get("src", "") if img_tag else ""
        caption = img_tag.get("alt", "新しい投稿がありました！") if img_tag else "新しい投稿がありました！"

        return {
            "id": shortcode,
            "url": actual_insta_url,
            "image": img_url,
            "caption": caption[:100] + ("..." if len(caption) > 100 else "")
        }
    except Exception as e:
        print(f"[{insta_id}] 取得エラー: {e}")
        return None

def send_to_discord(webhook_url, member_name, post_data):
    payload = {
        "username": f"{member_name} Instagram通知",
        "embeds": [
            {
                "title": f"{member_name}がInstagramを更新しました！",
                "url": post_data["url"],
                "description": post_data["caption"],
                "color": 15893389,
                "image": {"url": post_data["image"]} if post_data["image"] else {},
                "footer": {"text": "Instagram"}
            }
        ]
    }
    requests.post(webhook_url, json=payload, timeout=10)

def main():
    history = load_history()
    is_updated = False

    for member in MEMBERS:
        webhook_url = os.environ.get(member["webhook_env"])
        if not webhook_url:
            continue

        insta_id = member["insta_id"]
        latest = get_latest_post(insta_id)

        if not latest:
            continue

        last_id = history.get(insta_id)
        if last_id != latest["id"]:
            print(f"新着検知: {member['name']} ({latest['id']})")
            send_to_discord(webhook_url, member["name"], latest)
            history[insta_id] = latest["id"]
            is_updated = True

    if is_updated:
        save_history(history)

if __name__ == "__main__":
    main()
