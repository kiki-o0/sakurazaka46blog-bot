import os
import json
import requests
from bs4 import BeautifulSoup

# 各メンバーのクエリパラメータIDとDiscord Webhookの対応表
# ★テスト用に数人分だけ設定し、後から追加・編集できます
WEBHOOKS = {
    "04": os.environ.get("WEBHOOK_INOUE"),  # 井上梨名
    "05": os.environ.get("WEBHOOK_OZONO"),  # 大園玲
    "06": os.environ.get("WEBHOOK_ENDO"),   # 遠藤光莉
    # ※残りのメンバーも後ほどここにIDと名前を追加していきます
}

# 過去の最新記事URLを記憶しておくファイル名
CACHE_FILE = "last_blogs.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=4)

def check_blog():
    cache = load_cache()
    base_url = "https://sakurazaka46.com"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # 登録されているメンバーごとにチェック
    for member_id, webhook_url in WEBHOOKS.items():
        if not webhook_url:
            continue # Webhookが設定されていない場合はスキップ
            
        url = f"{base_url}?ct={member_id}"
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 最新のブログ記事を1件取得
            latest_post = soup.find("li", class_="box")
            if not latest_post:
                continue
                
            # 記事のURL、タイトル、画像などを抽出
            post_a = latest_post.find("a")
            post_url = "https://sakurazaka46.com" + post_a["href"]
            title = latest_post.find("p", class_="title").text.strip()
            name = latest_post.find("p", class_="name").text.strip()
            
            # サムネイル画像があれば取得
            img_tag = latest_post.find("div", class_="img").find("img")
            img_url = img_tag["src"] if img_tag else None
            
            # 前回チェック時とURLが違っていれば新しいブログが更新されたと判定
            if cache.get(member_id) != post_url:
                # 初回実行時は通知せずキャッシュに保存するだけ（大量通知を防ぐため）
                if member_id in cache:
                    send_discord(webhook_url, name, title, post_url, img_url)
                cache[member_id] = post_url
                
        except Exception as e:
            print(f"Error checking member {member_id}: {e}")
            
    save_cache(cache)

def send_discord(webhook_url, name, title, post_url, img_url):
    payload = {
        "embeds": [{
            "title": f"【ブログ更新】{title}",
            "url": post_url,
            "author": {"name": name},
            "color": 16738740 # 櫻色のカラーコード
        }]
    }
    if img_url:
        payload["embeds"][0]["image"] = {"url": img_url}
        
    requests.post(webhook_url, json=payload)

if __name__ == "__main__":
    check_blog()
