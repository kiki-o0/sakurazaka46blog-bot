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
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": f"sessionid={cookie_value}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"❌ 扉が閉まっています（エラー番号: {response.status_code}）")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        
        # 写真や詳しい文章の目印（OGPタグ）をしっかりキャッチするよ
        image_tag = soup.find("meta", property="property", content=True) # 予備
        img_url = ""
        img_tag_real = soup.find("meta", property="og:image")
        if img_tag_real:
            img_url = img_tag_real.get("content", "")

        desc_tag = soup.find("meta", property="og:description")
        caption = desc_tag.get("content", "Instagramが更新されました！") if desc_tag else "Instagramが更新されました！"
        
        print(f"✅ 写真と文章をキャッチしました！")

        return {
            "id": caption[:50], # 文章の最初の部分を記録用の目印にするよ
            "url": f"https://www.instagram.com/{insta_id}/",
            "caption": caption,
            "image": img_url
        }
    except Exception as e:
        print(f"❌ エラーになっちゃった: {e}")
        return None

def main():
    print("=== インスタ確認スタート ===")
    
    cookie_value = os.environ.get("INSTA_COOKIE")
    if not cookie_value:
        print("❌ 合鍵が見つからないよ！")
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
            print(f"✨ {member['name']} の新しい動きを発見！Discordへ送るね！")
            
            # 写真付きの綺麗なカード型（Embed）にしてDiscordへ飛ばすよ
            embed_data = {
                "title": f"{member['name']}のInstagramが更新されました！",
                "url": latest["url"],
                "color": 15893389,
                "description": latest["caption"]
            }
            if latest["image"]:
                embed_data["image"] = {"url": latest["image"]}

            payload = {
                "username": f"{member['name']} Instagram",
                "embeds": [embed_data]
            }
            requests.post(webhook_url, json=payload, timeout=10)
            history[member["insta_id"]] = latest["id"]
            is_updated = True
        else:
            print(f"➡️ {member['name']} の新しい動きはないみたい")

    if is_updated:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print("💾 記録をセーブしたよ")
        
    print("=== 確認終了 ===")

if __name__ == "__main__":
    main()
