import os
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("WEBHOOK_TEST_TEN")

def fetch_ten_blog_all_perfect():
    print("=== 天ちゃん公式ブログ：全画像コンプリート作戦 ===")
    
    list_url = "https://sakurazaka46.com/s/s46/diary/blog/list?ima=0000&ct=51"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        list_res = requests.get(list_url, headers=headers, timeout=10)
        list_res.encoding = list_res.apparent_encoding
        list_soup = BeautifulSoup(list_res.text, "html.parser")
        
        latest_box = list_soup.find("li", class_="box")
        link_tag = latest_box.find("a") if latest_box else None
        
        if not link_tag:
            print("❌ 住所が見つかりません。")
            return
            
        article_url = "https://sakurazaka46.com" + link_tag["href"]
        
        detail_res = requests.get(article_url, headers=headers, timeout=10)
        detail_res.encoding = detail_res.apparent_encoding
        detail_soup = BeautifulSoup(detail_res.text, "html.parser")
        
        title_tag = detail_soup.find("h1", class_="title")
        title = title_tag.text.strip() if title_tag else "タイトルが見つからないよ"
        
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
                    
        print(f"📝 タイトル: {title}")
        print(f"📸 見つけた画像: {len(image_urls)}枚")
        
        if WEBHOOK_URL:
            # 🛠️ 修正ポイント：10枚ずつに分けて、何回でもおつかいに行かせる！
            for i in range(0, len(image_urls), 10):
                # 10枚ずつ切り取る
                chunk = image_urls[i:i+10]
                embeds = []
                
                for j, img_url in enumerate(chunk):
                    # 一番最初の1枚目だけ、タイトルと住所を乗せる
                    if i == 0 and j == 0:
                        embeds.append({
                            "author": {"name": "山﨑 天"},
                            "title": title,
                            "url": article_url,
                            "color": 16777215,
                            "image": {"url": img_url}
                        })
                    else:
                        # 2枚目以降は「写真だけ」にする（これで4枚にまとめられず、大きく表示される！）
                        embeds.append({
                            "color": 16777215,
                            "image": {"url": img_url}
                        })
                        
                # Discordに配達！
                requests.post(WEBHOOK_URL, json={"username": "櫻坂通知ロボ", "embeds": embeds})
                
            print("📤 全ての画像をDiscordに送り届けました！")
            
    except Exception as e:
        print(f"💥 エラー: {e}")

if __name__ == "__main__":
    fetch_ten_blog_all_perfect()
