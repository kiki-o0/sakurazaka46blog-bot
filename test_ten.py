import os
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("WEBHOOK_TEST_TEN")

def fetch_ten_blog_perfect():
    print("=== 天ちゃん公式ブログ：真・お迎え作戦 ===")
    
    list_url = "https://sakurazaka46.com/s/s46/diary/blog/list?ima=0000&ct=51"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        list_res = requests.get(list_url, headers=headers, timeout=10)
        list_res.encoding = list_res.apparent_encoding
        list_soup = BeautifulSoup(list_res.text, "html.parser")
        
        # 罠1回避：ページ全体ではなく、確実に「天ちゃんの記事の箱」だけを狙う！
        latest_box = list_soup.find("li", class_="box")
        if not latest_box:
            print("❌ 記事の箱が見つかりません。")
            return
            
        link_tag = latest_box.find("a")
        if not link_tag or not link_tag.get("href"):
            print("❌ 住所が見つかりません。")
            return
            
        article_url = "https://sakurazaka46.com" + link_tag["href"]
        print(f"🔗 本物の住所: {article_url}")
        
        # 個別ページに潜入
        detail_res = requests.get(article_url, headers=headers, timeout=10)
        detail_res.encoding = detail_res.apparent_encoding
        detail_soup = BeautifulSoup(detail_res.text, "html.parser")
        
        title_tag = detail_soup.find(class_="title")
        title = title_tag.text.strip() if title_tag else "タイトルなし"
        
        # 罠2回避：絵文字やアイコンを無視して、本物の写真を探す！
        img_url = ""
        article_body = detail_soup.find(class_="box-article")
        if article_body:
            for img in article_body.find_all("img"):
                src = img.get("src", "")
                if "emoji" not in src and "icon" not in src:
                    img_url = src
                    if img_url.startswith("/"):
                        img_url = "https://sakurazaka46.com" + img_url
                    break
                    
        print(f"📝 タイトル: {title}")
        print(f"🖼️ 写真: {img_url}")
        
        # Discordへ送信
        if WEBHOOK_URL:
            embed = {
                "author": {"name": "山﨑 天"},
                "title": title,
                "url": article_url,
                "description": "天ちゃんの新しいブログが更新されたよ！",
                "color": 16777215
            }
            if img_url:
                embed["image"] = {"url": img_url}
                
            requests.post(WEBHOOK_URL, json={"username": "櫻坂通知ロボ", "embeds": [embed]})
            print("📤 真のカードを送信しました！")
            
    except Exception as e:
        print(f"💥 エラー: {e}")

if __name__ == "__main__":
    fetch_ten_blog_perfect()
