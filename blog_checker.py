import os
import json
import requests
from bs4 import BeautifulSoup

# 櫻坂46メンバー 2026年最新公式IDとSecrets名の対応表（全31名）
WEBHOOKS = {
    # 二期生
    "53": os.environ.get("WEBHOOK_ENDO_H"),  # 遠藤光莉
    "54": os.environ.get("WEBHOOK_OZONO"),   # 大園玲
    "55": os.environ.get("WEBHOOK_ONUMA"),   # 大沼晶保
    "56": os.environ.get("WEBHOOK_KOUSAKA"), # 幸阪茉里乃
    "57": os.environ.get("WEBHOOK_TAMURA"),  # 田村保乃
    "58": os.environ.get("WEBHOOK_FUJIYOSHI"),# 藤吉夏鈴
    "59": os.environ.get("WEBHOOK_MASUMOTO"), # 増本綺良
    "60": os.environ.get("WEBHOOK_MATSUDA"),  # 松田里奈
    "61": os.environ.get("WEBHOOK_MORITA"),   # 森田ひかる
    "62": os.environ.get("WEBHOOK_MORIYA"),   # 守屋麗奈
    "63": os.environ.get("WEBHOOK_YAMASAKI"), # 山﨑天
    # 三期生
    "64": os.environ.get("WEBHOOK_ISHIMORI"), # 石森璃花
    "65": os.environ.get("WEBHOOK_ENDO_R"),   # 遠藤理子
    "66": os.environ.get("WEBHOOK_ODAKURA"),  # 小田倉麗奈
    "67": os.environ.get("WEBHOOK_KOJIMA"),   # 小島凪紗
    "68": os.environ.get("WEBHOOK_TANIGUCHI"),# 谷口愛季
    "69": os.environ.get("WEBHOOK_NAKAJIMA"), # 中嶋優月
    "70": os.environ.get("WEBHOOK_MATONO"),   # 的野美青
    "71": os.environ.get("WEBHOOK_MUKAI"),    # 向井純葉
    "72": os.environ.get("WEBHOOK_MURAI"),    # 村井優
    "73": os.environ.get("WEBHOOK_MURAYAMA"), # 村山美羽
    "74": os.environ.get("WEBHOOK_YAMASHITA"),# 山下瞳月
    # 四期生
    "75": os.environ.get("WEBHOOK_ASAI"),     # 浅井恋乃未
    "76": os.environ.get("WEBHOOK_INAGUMA"),  # 稲熊ひな
    "77": os.environ.get("WEBHOOK_KATUMATA"), # 勝又春
    "78": os.environ.get("WEBHOOK_SATO"),     # 佐藤愛桜
    "79": os.environ.get("WEBHOOK_NAKAGAWA"), # 中川 智尋
    "80": os.environ.get("WEBHOOK_MATSUMOTO"),# 松本和子
    "81": os.environ.get("WEBHOOK_MEGURO"),   # 目黒陽色
    "82": os.environ.get("WEBHOOK_YAMAKAWA"), # 山川宇衣
    "83": os.environ.get("WEBHOOK_YAMADA"),   # 山田桃実
}

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
    
    for member_id, webhook_url in WEBHOOKS.items():
        if not webhook_url:
            continue
            
        url = f"{base_url}?ct={member_id}"
        try:
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            latest_post = soup.find("li", class_="box")
            if not latest_post:
                continue
                
            post_a = latest_post.find("a")
            post_url = "https://sakurazaka46.com" + post_a["href"]
            title = latest_post.find("p", class_="title").text.strip()
            name = latest_post.find("p", class_="name").text.strip()
            
            img_tag = latest_post.find("div", class_="img").find("img")
            img_url = img_tag["src"] if img_tag else None
            
            if cache.get(member_id) != post_url:
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
            "color": 16738740
        }]
    }
    if img_url:
        payload["embeds"][0]["image"] = {"url": img_url} # バグ修正: embedsの配列内にimageを正しく配置
        
    requests.post(webhook_url, json=payload)

if __name__ == "__main__":
    check_blog()
