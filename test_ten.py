import os
import json
import requests
from bs4 import BeautifulSoup

# テスト用のWebhook（山﨑天ちゃん専用チャンネルのもの）
# 後ほどGitHubのSecretsに登録するか、ここに直接テスト用URLを貼ってもOKです！
WEBHOOK_URL = os.environ.get("WEBHOOK_TEST_TEN")

def test_extract():
    print("=== 山﨑天ちゃんデータ持ち帰り実験スタート ===")
    
    insta_id = "yamasaki.ten"
    fetch_url = f"https://www.instagram.com/{insta_id}/"
    
    # 警備員対策の変装用ヘッダー
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": f"sessionid={os.environ.get('INSTA_COOKIE', '')}"
    }
    
    try:
        response = requests.get(fetch_url, headers=headers, timeout=15)
        print(f"📡 Instagramからの返事: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ ページに入れませんでした…")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        
        # ページ全体の構造から、隠れているデータ（文字や画像のヒント）を探す！
        desc_tag = soup.find("meta", property="og:description")
        caption = desc_tag.get("content", "データなし") if desc_tag else "データなし"
        
        img_tag = soup.find("meta", property="og:image")
        image_url = img_tag.get("content", "画像データなし") if img_tag else "画像データなし"

        print(f"📝 持ち帰った文章: {caption}")
        print(f"🖼️ 持ち帰った画像の住所: {image_url}")

        # Discordのテスト部屋に、持ち帰れたデータをそのまま送ってみる！
        if WEBHOOK_URL:
            payload = {
                "username": "天ちゃんデータ実験室",
                "embeds": [{
                    "title": "実験結果：持ち帰れたデータ",
                    "description": f"**文章:**\n{caption}\n\n**画像の住所:**\n{image_url}",
                    "color": 65280
                }]
            }
            if image_url.startswith("http"):
                # もし画像の住所が取れていれば、Discordに直接画像カードを表示させてみる！
                payload["embeds"][0]["image"] = {"url": image_url}
                
            requests.post(WEBHOOK_URL, json=payload, timeout=10)
            print("📤 テスト部屋へデータを送信しました！")
        else:
            print("⚠️ WEBHOOK_TEST_TEN の住所が設定されていないよ！")

    except Exception as e:
        print(f"💥 エラー発生: {e}")

    print("=== 実験終了 ===")

if __name__ == "__main__":
    test_extract()

