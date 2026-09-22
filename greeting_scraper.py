import os
import json
import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# 設定
TARGET_URL = "https://sakurazaka46.com/s/s46/page/greeting"
STATE_FILE = "greeting_state.json"
RSS_FILE = "greeting_rss.xml"
IMAGE_DIR = "greeting_images"

def main():
    # 現在の年月を取得 (例: "2026-09")
    now = datetime.datetime.now()
    current_year_month = now.strftime("%Y-%m")
    
    # 状態ファイル読み込み（今月分がすでに取得済みか確認）
    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}
            
    last_fetched_month = state.get("last_fetched_month")
    
    # すでに今月分を取得済みの場合はスキップ
    if last_fetched_month == current_year_month:
        print(f"今月({current_year_month})分はすでに取得済みです。処理を終了します。")
        return

    print(f"グリーティングページ ({TARGET_URL}) の取得を開始します...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(TARGET_URL, headers=headers)
    if response.status_code != 200:
        print(f"ページの取得に失敗しました。ステータスコード: {response.status_code}")
        return
        
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 画像保存ディレクトリの作成
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    # ページ内の画像を解析（メンバーごとのカード・フォトの画像を抽出）
    images_info = []
    seen_urls = set()
    
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src and "/images/" in src:
            # 絶対パスに変換
            if src.startswith("//"):
                img_url = "https:" + src
            elif src.startswith("/"):
                img_url = "https://sakurazaka46.com" + src
            elif src.startswith("http"):
                img_url = src
            else:
                continue
                
            # 重複を排除しつつリストに追加
            if img_url not in seen_urls:
                seen_urls.add(img_url)
                images_info.append(img_url)
                
    print(f"検出された画像数: {len(images_info)}件")
    
    # 画像をダウンロード（ローカルに保存）
    downloaded_images = []
    for i, img_url in enumerate(images_info):
        try:
            img_res = requests.get(img_url, headers=headers, timeout=10)
            if img_res.status_code == 200:
                filename = f"{current_year_month}_{i+1}.jpg"
                filepath = os.path.join(IMAGE_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(img_res.content)
                downloaded_images.append({
                    "url": img_url,
                    "local_path": filepath
                })
        except Exception as e:
            print(f"画像のダウンロードに失敗しました ({img_url}): {e}")

    # RSS (Atom/XML) の生成
    rss_root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss_root, "channel")
    
    title_elem = ET.SubElement(channel, "title")
    title_elem.text = f"櫻坂46 グリーティング ({current_year_month})"
    
    link_elem = ET.SubElement(channel, "link")
    link_elem.text = TARGET_URL
    
    desc_elem = ET.SubElement(channel, "description")
    desc_elem.text = f"櫻坂46 グリーティングページ更新情報 ({current_year_month})"
    
    item = ET.SubElement(channel, "item")
    item_title = ET.SubElement(item, "title")
    item_title.text = f"櫻坂46 グリーティングカード・フォト ({current_year_month})"
    
    item_link = ET.SubElement(item, "link")
    item_link.text = TARGET_URL
    
    item_guid = ET.SubElement(item, "guid")
    item_guid.text = f"sakurazaka46-greeting-{current_year_month}"
    
    item_pub = ET.SubElement(item, "pubDate")
    item_pub.text = now.strftime("%a, %d %b %Y %H:%M:%S +0900")
    
    item_desc = ET.SubElement(item, "description")
    desc_html = f"<p>{current_year_month}度のグリーティング画像が更新されました。</p>"
    for img in downloaded_images:
        # 画像をリンク(<a>)で囲み、タップで元画像URLを開けるように修正
        desc_html += f'<br><a href="{img["url"]}" target="_blank"><img src="{img["url"]}" style="max-width:100%;" /></a>'
    item_desc.text = desc_html

    tree = ET.ElementTree(rss_root)
    tree.write(RSS_FILE, encoding="utf-8", xml_declaration=True)
    print(f"RSSファイルを生成しました: {RSS_FILE}")

    # 状態を保存（今月分を取得済みとして記録）
    state["last_fetched_month"] = current_year_month
    state["updated_at"] = now.isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        
    print("今月分の処理が完了しました。")

if __name__ == "__main__":
    main()
