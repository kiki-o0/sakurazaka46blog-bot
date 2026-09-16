import os
import json
import requests

WEBHOOK_URL = os.environ.get("WEBHOOK_TEST_TEN")

def test_timeline_extract():
    print("=== タイムラインのぞき見実験スタート ===")
    
    # プロフィールではなく「タイムライン（自分のホーム画面）」の合図に突撃する！
    fetch_url = "https://www.instagram.com/api/v1/feed/timeline/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": f"sessionid={os.environ.get('INSTA_COOKIE', '')}",
        # ※Instagramの裏の合図に話しかけるときは、この特別な合言葉が必要になります！
        "X-IG-App-ID": "936619743392459" 
    }
    
    try:
        response = requests.get(fetch_url, headers=headers, timeout=15)
        print(f"📡 タイムラインからの返事: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ タイムラインに入れませんでした… (返事: {response.status_code})")
            return

        # 帰ってきたデータをパズルみたいに解読する
        data = response.json()
        
        # タイムラインに流れてきた最新の投稿をチェック！
        items = data.get("items", [])
        if items:
            print(f"✨ 投稿が見つかりました！（合計 {len(items)} 件）")
            # とりあえず一番上の最新のものの情報を少しだけDiscordに送ってみる
            first_item = items[0]
            caption_text = first_item.get("caption", {}).get("text", "文章なし")
            
            if WEBHOOK_URL:
                payload = {
                    "username": "タイムライン実験室",
                    "embeds": [{
                        "title": "タイムラインからの拾い物成功！",
                        "description": f"**最初の文章:**\n{caption_text[:100]}...",
                        "color": 65280
                    }]
                }
                requests.post(WEBHOOK_URL, json=payload, timeout=10)
                print("📤 Discordにテスト送信しました！")
        else:
            print("📭 投稿が何も流れてきませんでした…")

    except Exception as e:
        print(f"💥 エラー発生: {e}")

    print("=== 実験終了 ===")

if __name__ == "__main__":
    test_timeline_extract()
