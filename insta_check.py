import os
import json
import requests
from bs4 import BeautifulSoup

MEMBERS = [
    {"name": "山﨑天", "insta_id": "yamasaki.ten", "webhook_env": "WEBHOOK_TEN"},
    {"name": "谷口愛季", "insta_id": "airi.taniguchi.official", "webhook_env": "WEBHOOK_AIRI"},
]

HISTORY_FILE = "insta_history.json"

def get_latest_post(insta_id):
    print(f"👀 {insta_id} を別ルート(Picuki)で確認中...")
    url = f"https://www.picuki.com/profile/{insta_id}"
    # ロボットっぽさを消すための変装
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ アクセス拒否（エラー番号: {response.status_code}）")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        # 最新の投稿のリンクを探す
        post_link_tag = soup.select_one(".box-photo a")
        
        if not post_link_tag:
            print("❌ 投稿が見つかりません")
            return None

        post_url = post_link_tag.get("href", "")
        
        # URLから投稿IDを抜き出す
        post_id = post_url.split("/")[-1]
        if not post_id:
            return None
            
        print(f"✅ 最新投稿を発見: {post_id}")

        # PicukiのURLをそのまま送ることで、ログイン不要で確実に見られます
        return {
            "id": post_id,
            "url": post_url,
            "caption": "Instagramが更新されました！（リンク先から見られます）"
        }
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def main():
    print("=== インスタ確認スタート ===")
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass

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
                "username": f"{member['name']} Instagram通知",
                "embeds": [{
                    "title": f"{member['name']}がInstagramを更新しました！", 
                    "url": latest["url"], 
                    "color": 15893389, 
                    "description": latest["caption"]
                }]
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
