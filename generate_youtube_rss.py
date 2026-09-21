import requests
import xml.etree.ElementTree as ET
import urllib.parse
from datetime import datetime

def process_channel(url, output_file):
    # rss2json API経由で取得し、YouTube側のBotブロックを回避する。エラー原因となったキャッシュ回避用のダミーパラメータは削除。
    encoded_url = urllib.parse.quote(url)
    api_url = f"https://api.rss2json.com/v1/api.json?rss_url={encoded_url}"
    
    try:
        response = requests.get(api_url, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "ok":
            print(f"Skipped: rss2json API returned error for {url}")
            return False
            
    except Exception as e:
        print(f"Request Error for {url}: {e}")
        return False
        
    # Atom形式のXMLを新しく構築
    ET.register_namespace('', 'http://www.w3.org/2005/Atom')
    feed = ET.Element('{http://www.w3.org/2005/Atom}feed')
    
    # フィードのタイトルとリンク
    feed_title = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}title')
    feed_title.text = data.get("feed", {}).get("title", "YouTube Channel")
    
    feed_link = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}link')
    feed_link.set('href', url)
    
    feed_updated = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}updated')
    feed_updated.text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # 各動画のデータを処理して追加
    for item in data.get("items", []):
        entry = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}entry')
        
        # タイトル
        title = ET.SubElement(entry, '{http://www.w3.org/2005/Atom}title')
        title.text = item.get("title", "")
        
        # リンク
        link = ET.SubElement(entry, '{http://www.w3.org/2005/Atom}link')
        link.set('href', item.get("link", ""))
        
        # ID
        entry_id = ET.SubElement(entry, '{http://www.w3.org/2005/Atom}id')
        entry_id.text = item.get("guid", item.get("link", ""))
        
        # 更新日時
        pub_date_str = item.get("pubDate", "")
        updated = ET.SubElement(entry, '{http://www.w3.org/2005/Atom}updated')
        try:
            # rss2json API は "YYYY-MM-DD HH:MM:SS" 形式で返すため、Atom向けに変換
            dt = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S")
            updated.text = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            updated.text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            
        # 本文（サムネイル画像＋概要文）
        content = ET.SubElement(entry, '{http://www.w3.org/2005/Atom}content')
        content.set('type', 'html')
        
        thumbnail_url = item.get("thumbnail", "")
        description = item.get("description", "")
        
        html_content = ""
        if thumbnail_url:
            # Feederできれいに表示されるように画像を埋め込み
            html_content += f'<img src="{thumbnail_url}" alt="thumbnail">'
        
        if description:
            escaped_desc = description.replace('\n', '<br>')
            html_content += f'<br><br>{escaped_desc}'
            
        content.text = html_content
        
    tree = ET.ElementTree(feed)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    return True

def main():
    channels = [
        {
            "name": "櫻坂46 OFFICIAL YouTube CHANNEL",
            "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCmr9bYmymcBmQ1p2tLBRvwg",
            "output_file": "youtube_official_rss.xml"
        },
        {
            "name": "櫻坂チャンネル",
            "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCDNDlqJRz4FsO_ByfUNOSuQ",
            "output_file": "youtube_sakurazaka_channel_rss.xml"
        }
    ]
    
    for ch in channels:
        print(f"Processing {ch['name']}...")
        success = process_channel(ch["url"], ch["output_file"])
        if success:
            print(f"Success: {ch['name']} -> {ch['output_file']}")

if __name__ == "__main__":
    main()
