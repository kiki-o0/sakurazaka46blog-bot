import os
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("WEBHOOK_TEST_TEN")

def fetch_ten_blog_all():
    print("=== 天ちゃん公式ブログ：全画像お迎え作戦 ===")
    
    list_url = "https://sakurazaka46.com/s/s46/diary/blog/list?ima=0000&ct=51"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        # 1. 一覧ページから最新記事の住所をゲット
        list_res = requests.get(list_url, headers=headers, timeout=10)
        list_res.encoding = list_res.apparent_encoding
        list_soup = BeautifulSoup(list_res.text, "html.parser")
        
        latest_box = list_soup.find("li", class_="box")
        link_tag = latest_box.find("a") if latest_box else None
        
        if not link_tag:
            print("❌ 住所が見つかりません。")
            return
            
        article_url = "https://sakurazaka46.com" + link_tag["href"]
        
        # 2. 個別ページに潜入
        detail_res = requests.get(article_url, headers=headers, timeout=10)
        detail_res.encoding = detail_res.apparent_encoding
        detail_soup = BeautifulSoup(detail_res.text, "html.parser")
        
        # 🛠️ 修正ポイント1：看板ではなく、記事の「大見出し（h1）」のタイトルをピンポイントで狙う！
        title_tag = detail_soup.find("h1", class_="title")
        title = title_tag.text.strip() if title_tag else "タイトルが見つからないよ"
        
        # 🛠️ 修正ポイント2：画像を「全部」拾い集める！
        image_urls = []
        article_body = detail_soup.find(class_="box-article")
        if article_body:
            for img in article_body.find_all("img"):
                src = img.get("src", "")
                # 絵文字やアイコンは無視する
                if "emoji" not in src and "icon" not in src:
                    img_url = src
                    if img_url.startswith("/"):
                        img_url = "https://sakurazaka46.com" + img_url
                    image_urls.append(img_url)
                    
        print(f"📝 修正したタイトル: {title}")
        print(f"📸 見つけた画像: {len(image_urls)}枚")
        
        # 3. Discordに「アルバム形式」で送る
        if WEBHOOK_URL:
            embeds = []
            
            if image_urls:
                # Discordは1回の送信で10枚までなので、最初の10枚に絞る
                for i, img_url in enumerate(image_urls[:10]):
                    if i == 0:
                        # 1枚目のカードにはタイトルなどの情報を全部載せる
                        embeds.append({
                            "author": {"name": "山﨑 天"},
                            "title": title,
                            "url": article_url,
                            "color": 16777215,
                            "image": {"url": img_url}
                        })
                    else:
                        # 2枚目以降は「同じ住所」と「画像」だけにする（これがまとめる裏技！）
                        embeds.append({
                            "url": article_url,
                            "image": {"url": img_url}
                        })
            else:
                # もし画像が1枚もないブログだった場合
                embeds.append({
                    "author": {"name": "山﨑 天"},
                    "title": title,
                    "url": article_url,
                    "description": "このブログに画像はありませんでした。",
                    "color": 16777215
                })
                
            requests.post(WEBHOOK_URL, json={"username": "櫻坂通知ロボ", "embeds": embeds})
            print("📤 全画像付きの完璧なカードを送信しました！")
            
    except Exception as e:
        print(f"💥 エラー: {e}")

if __name__ == "__main__":
    fetch_ten_blog_all()
