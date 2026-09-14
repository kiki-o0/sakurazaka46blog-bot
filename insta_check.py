import os
import re
import json
import requests

MEMBERS = [
    {"name": "山﨑天", "insta_id": "yamasaki.ten", "webhook_env": "WEBHOOK_TEN"},
    {"name": "谷口愛季", "insta_id": "airi.taniguchi.official", "webhook_env": "WEBHOOK_AIRI"},
]

HISTORY_FILE = "insta_history.json"

# ▼ VercelのURL（https://〇〇.vercel.app）があれば書き換えると最強の抜け道になります ▼
RSSHUB_BASE = "https://rsshub.app"

def get_latest_post(insta_id):
    print(f"👀 {insta_id} のRSSHubを確認中...")
    # ロボットが読みやすいJSONフォーマットで取得
    url = f"{RSSHUB_BASE}/instagram/user/{insta_id}?format=json"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ アクセス拒否（エラー番号: {response.status_code}）")
            return None

        data = response.json()
        items = data.get("items", [])
        
        if not items:
            print("❌ 投稿データが空です")
            return None

        # 一番新しい投稿を抜き出す
        latest_post = items[0]
        post_url = latest_post.get("url") or latest_post.get("id", "")
        
        # URLから投稿固有のID（ショートコード）を切り出す
        match = re.search(r'/(?:p|post|reel)/([^/?]+)', post_url)
        shortcode = match.group(1) if match else "unknown_id"
        
        print(f"✅ 最新投稿を発見: {shortcode}")

        return {
            "id": shortcode,
            "url": f"https://www.instagram.com/p/{shortcode}/",
            "caption": latest_post.get("title", "新しい投稿があります！")[:100]
        }
    except Exception as e:
        print(f"❌ エラー: {e}")
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
            print(f"➡️ {member['name']} の更新なし")

    if is_updated:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print("💾 記録をセーブしました")
        
    print("=== 確認終了 ===")

if __name__ == "__main__":
    main()
