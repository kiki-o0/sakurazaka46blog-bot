import os
import json
import requests
from bs4 import BeautifulSoup

WEBHOOKS = {
    "53": os.environ.get("WEBHOOK_ENDO_H"), "54": os.environ.get("WEBHOOK_OZONO"),
    "55": os.environ.get("WEBHOOK_ONUMA"), "56": os.environ.get("WEBHOOK_KOUSAKA"),
    "57": os.environ.get("WEBHOOK_TAMURA"), "58": os.environ.get("WEBHOOK_FUJIYOSHI"),
    "59": os.environ.get("WEBHOOK_MASUMOTO"), "60": os.environ.get("WEBHOOK_MATSUDA"),
    "61": os.environ.get("WEBHOOK_MORITA"), "62": os.environ.get("WEBHOOK_MORIYA"),
    "63": os.environ.get("WEBHOOK_YAMASAKI"), "64": os.environ.get("WEBHOOK_ISHIMORI"),
    "65": os.environ.get("WEBHOOK_ENDO_R"), "66": os.environ.get("WEBHOOK_ODAKURA"),
    "67": os.environ.get("WEBHOOK_KOJIMA"), "68": os.environ.get("WEBHOOK_TANIGUCHI"),
    "69": os.environ.get("WEBHOOK_NAKAJIMA"), "70": os.environ.get("WEBHOOK_MATONO"),
    "71": os.environ.get("WEBHOOK_MUKAI"), "72": os.environ.get("WEBHOOK_MURAI"),
    "73": os.environ.get("WEBHOOK_MURAYAMA"), "74": os.environ.get("WEBHOOK_YAMASHITA"),
    "75": os.environ.get("WEBHOOK_ASAI"), "76": os.environ.get("WEBHOOK_INAGUMA"),
    "77": os.environ.get("WEBHOOK_KATUMATA"), "78": os.environ.get("WEBHOOK_SATO"),
    "79": os.environ.get("WEBHOOK_NAKAGAWA"), "80": os.environ.get("WEBHOOK_MATSUMOTO"),
    "81": os.environ.get("WEBHOOK_MEGURO"), "82": os.environ.get("WEBHOOK_YAMAKAWA"),
    "83": os.environ.get("WEBHOOK_YAMADA"),
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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for member_id, webhook_url in WEBHOOKS.items():
        if not webhook_url:
            continue
            
        url = f"https://sakurazaka46.com/s/s46/diary/blog/list?ct={member_id}"
        
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, "html.parser")
            
            latest_post = soup.find("li", class_="box")
            if not latest_post:
                continue
                
            post_a = latest_post.find("a")
            if not post_a:
                continue
            post_url = "https://sakurazaka46.com" + post_a["href"]
            
            # 【修正点】タイトルと名前がない場合はパニックにならずスキップする安全装置
            title_tag = latest_post.find("p", class_="title")
            name_tag = latest_post.find("p", class_="name")
            if not title_tag or not name_tag:
                continue
                
            title = title_tag.text.strip()
            name = name_tag.text.strip()
            
            img_tag = latest_post.find("div", class_="img").find("img") if latest_post.find("div", class_="img") else None
            img_url = img_tag["src"] if img_tag else None
            if img_url and not img_url.startswith("http"):
                img_url = "https://sakurazaka46.com" + img_url

            if cache.get(member_id) != post_url:
                if member_id in cache:
                    send_discord(webhook_url, name, title, post_url, img_url)
                cache[member_id] = post_url
                
        except Exception as e:
            print(f"[{member_id}] エラー: {e}")
            
    save_cache(cache)

def send_discord(webhook_url, name, title, post_url, img_url):
    payload = {
        "embeds": [{
            "title": f"【ブログ更新】{title}",
            "url": post_url,
            "author": {"name": name},
            "color": 16738740
        }]
    }
    if img_url:
        payload["embeds"][0]["image"] = {"url": img_url}
    requests.post(webhook_url, json=payload, timeout=10)

if __name__ == "__main__":
    check_blog()
