import os
import json
import requests
from bs4 import BeautifulSoup
import time

# ！！！ここが真の背番号リストです！！！
WEBHOOKS = {
    # 2期生
    "46": os.environ.get("WEBHOOK_TAMURA"),
    "47": os.environ.get("WEBHOOK_FUJIYOSHI"),
    "48": os.environ.get("WEBHOOK_MATSUDA"),
    "50": os.environ.get("WEBHOOK_MORITA"),
    "51": os.environ.get("WEBHOOK_YAMASAKI"), # 天ちゃん！
    
    # 新2期生
    "53": os.environ.get("WEBHOOK_ENDO_H"), # ひかりん！
    "54": os.environ.get("WEBHOOK_OZONO"),
    "55": os.environ.get("WEBHOOK_ONUMA"),
    "56": os.environ.get("WEBHOOK_KOUSAKA"),
    "57": os.environ.get("WEBHOOK_MASUMOTO"),
    "58": os.environ.get("WEBHOOK_MORIYA"),
    
    # 3期生
    "59": os.environ.get("WEBHOOK_ISHIMORI"),
    "60": os.environ.get("WEBHOOK_ENDO_R"),
    "61": os.environ.get("WEBHOOK_ODAKURA"),
    "62": os.environ.get("WEBHOOK_KOJIMA"), # 小島凪紗ちゃん！
    "63": os.environ.get("WEBHOOK_TANIGUCHI"),
    "64": os.environ.get("WEBHOOK_NAKAJIMA"),
    "65": os.environ.get("WEBHOOK_MATONO"),
    "66": os.environ.get("WEBHOOK_MUKAI"),
    "67": os.environ.get("WEBHOOK_MURAI"),
    "68": os.environ.get("WEBHOOK_MURAYAMA"),
    "69": os.environ.get("WEBHOOK_YAMASHITA"), # 山下瞳月ちゃん！
    
    # 4期生
    "70": os.environ.get("WEBHOOK_ASAI"),
    "71": os.environ.get("WEBHOOK_INAGUMA"),
    "72": os.environ.get("WEBHOOK_KATUMATA"),
    "73": os.environ.get("WEBHOOK_SATO"),
    "74": os.environ.get("WEBHOOK_NAKAGAWA"),
    "75": os.environ.get("WEBHOOK_MATSUMOTO"),
    "76": os.environ.get("WEBHOOK_MEGURO"),
    "77": os.environ.get("WEBHOOK_YAMAKAWA"),
    "78": os.environ.get("WEBHOOK_YAMADA"),
}

CACHE_FILE = "last_blogs.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def check_blog():
    cache = load_cache()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }

    print("=== ブログ確認スタート ===")
    for member_id, webhook_url in WEBHOOKS.items():
        if not webhook_url:
            continue
            
        url = f"https://sakurazaka46.com/s/s46/diary/blog/list?ct={member_id}"
        
        try:
            res = requests.get(url, headers=headers, timeout=15)
            res.encoding = res.apparent_encoding
            
            if res.status_code != 200:
                print(f"[{member_id}] ⚠️ エラー: {res.status_code}")
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            
            latest_post = soup.find("li", class_="box")
            if not latest_post:
                continue
                
            post_a = latest_post.find("a")
            if not post_a:
                continue
            post_url = "https://sakurazaka46.com" + post_a["href"]

            name_tag = latest_post.find(class_="name")
            name = name_tag.text.strip() if name_tag else "メンバー"

            if cache.get(member_id) == post_url:
                print(f"[{member_id}] ➡️ 新しい記事はないみたいです")
                continue
            
            print(f"[{member_id}] 🚪 新しい記事を発見！奥の部屋（個別記事）に入ります...")
            time.sleep(1) 

            detail_res = requests.get(post_url, headers=headers, timeout=15)
            detail_res.encoding = detail_res.apparent_encoding
            detail_soup = BeautifulSoup(detail_res.text, "html.parser")

            title_tag = detail_soup.find("h1", class_="title")
            title = title_tag.text.strip() if title_tag else "タイトルなし"
            
            image_urls = []
            article_body = detail_soup.find(class_="box-article")
            if article_body:
                for img in article_body.find_all("img"):
                    src = img.get("src", "")
                    if "emoji" not in src and "icon" not in src:
                        img_url = src
                        if img_url.startswith("/"):
                            img_url = "https://sakurazaka46.com" + img_url
                        image_urls.append(img_url)

            if member_id in cache:
                print(f"[{member_id}] ✨ 新しいブログ発見！Discordに送ります！（画像{len(image_urls)}枚）")
                send_discord_album(webhook_url, name, title, post_url, image_urls)
            else:
                print(f"[{member_id}] 📝 初回の記録としてメモ帳に書きました（通知はしません）")
                
            cache[member_id] = post_url
                
        except Exception as e:
            print(f"[{member_id}] エラー: {e}")
            
    save_cache(cache)
    print("=== 確認終了 ===")

def send_discord_album(webhook_url, name, title, post_url, image_urls):
    if not image_urls:
        payload = {
            "username": "櫻坂blog通知",
            "embeds": [{
                "author": {"name": name},
                "title": f"【ブログ更新】{title}",
                "url": post_url,
                "description": "このブログに画像はありませんでした。",
                "color": 16738740
            }]
        }
        requests.post(webhook_url, json=payload, timeout=10)
        return

    for i in range(0, len(image_urls), 10):
        chunk = image_urls[i:i+10]
        embeds = []
        
        for j, img_url in enumerate(chunk):
            if i == 0 and j == 0:
                embeds.append({
                    "author": {"name": name},
                    "title": f"【ブログ更新】{title}",
                    "url": post_url,
                    "color": 16738740,
                    "image": {"url": img_url}
                })
            else:
                embeds.append({
                    "color": 16738740,
                    "image": {"url": img_url}
                })
                
        requests.post(webhook_url, json={"username": "櫻坂通知ロボ", "embeds": embeds}, timeout=10)

if __name__ == "__main__":
    check_blog()
