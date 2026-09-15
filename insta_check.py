import os
import json
import requests
from bs4 import BeautifulSoup

MEMBERS = [
    {"name": "山﨑天", "insta_id": "yamasaki.ten", "webhook_env": "WEBHOOK_TEN"},
    {"name": "谷口愛季", "insta_id": "airi.taniguchi.official", "webhook_env": "WEBHOOK_AIRI"},
]

HISTORY_FILE = "insta_history.json"

def get_latest_post_with_cookie(insta_id, cookie_value):
    print(f"👀 合鍵を使って {insta_id} のページを確認中...")
    url = f"https://www.instagram.com/{insta_id}/"
    
    # 人間になりすますための変装道具と、あなたの持っている「合鍵(Cookie)」をセットする
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": f"sessionid={cookie_value}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ 合鍵が合わないか、アクセス拒否されました（エラー番号: {response.status_code}）")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Instagramのページから最新の投稿を探す
        # （メタタグという裏側のデータから最新の情報をキレイに抜き出します）
        meta_tag = soup.find("meta", property="og:description")
        if not meta_tag:
            print("❌ 投稿のデータが見つかりませんでした")
            return None
            
        content = meta_tag.get("content", "")
        print(f"✅ ページの中身を無事に読み込めました！")

        # 適当なIDの代わりに最新ページの文字を記録用にする
        return {
            "id": content[:50],  # 最初の50文字を合言葉にする
            "url": f"https://www.instagram.com/{insta_id}/",
            "caption": content
        }
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        return None

def main():
    print("=== インスタ確認スタート ===")
    
    # 秘密の引き出しからあなたの「合鍵(sessionid)」を取り出す
    cookie_value = os.environ.get("INSTA_COOKIE")
    if not cookie_value:
        print("❌ 合鍵(INSTA_COOKIE)がGitHubのSecretsに見つかりません！")
        return

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

        latest = get_latest_post_with_cookie(member["insta_id"], cookie_value)
        if not latest:
            continue

        last_id = history.get(member["insta_id"])
        if last_id != latest["id"]:
            print(f"✨ {member['name']} のページに新しい動きがあります！Discordへ送ります！")
            payload = {
                "username": f"{member['name']} Instagram",
                "embeds": [{
                    "title": f"{member['name']}のInstagramページに動きがあります！", 
                    "url": latest["url"], 
                    "color": 15893389,
                    "description": latest["caption"][:200] + "..."
                }]
            }
            requests.post(webhook_url, json=payload, timeout=10)
            history[member["insta_id"]] = latest["id"]
            is_updated = True
        else:
            print(f"➡️ {member['name']} の新しい動きはありません")

    if is_updated:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print("💾 記録をセーブしました")
        
    print("=== 確認終了 ===")

if __name__ == "__main__":
    main()
