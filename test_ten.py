import os
import requests
from bs4 import BeautifulSoup

# 天ちゃんテスト部屋の住所
WEBHOOK_URL = os.environ.get("WEBHOOK_TEST_TEN")

def fetch_ten_blog():
    print("=== 天ちゃん公式ブログお迎え作戦スタート ===")
    
    # 1. 櫻坂46公式サイトの「山﨑天ちゃんの個別ブログ一覧」の住所
    # （ct=53 が天ちゃんの背番号みたいなものです！）
    url = "https://sakurazaka46.com/s/s46/diary/blog/list?ima=0000&ct=53"
    
    # ロボット感を少し消すための軽い変装
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        # 2. ブログのページにアクセス！
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding
        
        if response.status_code == 200:
            print("✅ 天ちゃんのブログページに入れました！")
            
            # 3. ページの中身（設計図）を読み解く
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 4. 「最新の投稿のデータ」を探す
            # 公式ブログの仕組み上、一番最初に出てくる記事の箱（box）を探します
            latest_article = soup.find("li", class_="box")
            
            if latest_article:
                # ブログタイトル取得
                title_tag = latest_article.find("h1", class_="title")
                title = title_tag.text.strip() if title_tag else "タイトルなし"
                
                # 画像データ取得（記事のURL）
                # ※公式は一覧ページに画像がないことが多いので、まずは記事のリンク先を取ります
                link_tag = latest_article.find("a")
                article_link = "https://sakurazaka46.com" + link_tag["href"] if link_tag else url
                
                print(f"📝 見つけたタイトル: {title}")
                print(f"🔗 記事の住所: {article_link}")
                
                # 5. Discordに綺麗に送る
                if WEBHOOK_URL:
                    payload = {
                        "username": "櫻坂46 ブログ通知ロボ",
                        "embeds": [
                            {
                                "author": {"name": "山﨑 天"},
                                "title": title,
                                "url": article_link,
                                "description": "天ちゃんの新しいブログが更新されたよ！",
                                "color": 16777215 # 櫻坂のイメージカラー（白）
                            }
                        ]
                    }
                    requests.post(WEBHOOK_URL, json=payload)
                    print("📤 天ちゃんの部屋に通知を送りました！")
            else:
                print("⚠️ 記事の箱が見つかりませんでした。")
        else:
            print(f"❌ ページに入れませんでした（お返事: {response.status_code}）")
            
    except Exception as e:
        print(f"💥 エラー発生: {e}")

if __name__ == "__main__":
    fetch_ten_blog()
