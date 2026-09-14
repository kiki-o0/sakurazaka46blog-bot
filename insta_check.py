import os
import re
import json
import requests
from bs4 import BeautifulSoup

MEMBERS = [
    {"name": "山﨑天", "insta_id": "yamasaki.ten", "webhook_env": "WEBHOOK_TEN"},
    {"name": "谷口愛季", "insta_id": "airi.taniguchi.official", "webhook_env": "WEBHOOK_AIRI"},
]

HISTORY_FILE = "insta_history.json"

def get_latest_post(insta_id):
    print(f"👀 {insta_id} のページを確認中...")
    url = f"https://www.picnob.com/profile/{insta_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ アクセス拒否（エラー番号: {response.status_code}）")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        post_item = soup.select_one(".posts .post-item a")
        
        if not post_item:
            print("❌ 投稿が見つからないか、サイトの構造が変わっています")
            return None

        post_link = post_item.get("href", "")
        shortcode_match = re.search(r'/post/([^/]+)/', post_link)
        if not shortcode_match:
            print("❌ 投稿の固有IDが見つかりません")
            return None

        shortcode = shortcode_match.group(1)
        print(f"✅ 最新投稿を発見: {shortcode}")
        
        return {
            "id": shortcode,
            "url": f"https://www.instagram.com/p/{shortcode}/",
            "image": "",
            "caption": "新しい投稿があります！"
        }
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        return None

def main():
    print("=== インスタ確認スタート ===")
    history = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    is_updated = False

    for member in MEMBERS:
        webhook_url = os.environ.get(member["webhook_env"])
        if not webhook_url:
            print(f"⚠️ {member['name']} の通知先(Webhook)が見つかりません")
            continue

        latest = get_latest_post(member["insta_id"])
        if not latest:
            continue

        last_id = history.get(member["insta_id"])
        if last_id != latest["id"]:
            print(f"✨ {member['name']} の新着をDiscordへ送ります！")
            
            payload = {
                "username": f"{member['name']} Instagram",
                "embeds": [{"title": f"{member['name']}がInstagramを更新しました！", "url": latest["url"], "color": 15893389}]
            }
            requests.post(webhook_url, json=payload, timeout=10)
            
            history[member["insta_id"]] = latest["id"]
            is_updated = True
        else:
            print(f"➡️ {member['name']} の新しい投稿はありません")

    if is_updated:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print("💾 新しい記録をセーブしました")
        
    print("=== 確認終了 ===")

if __name__ == "__main__":
    main()
