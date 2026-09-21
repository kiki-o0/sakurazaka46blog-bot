import requests
import xml.etree.ElementTree as ET
import urllib.parse
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

def fetch_xml(channel_id):
    # 複数のRSSHub公開サーバーを巡回し、YouTubeのBotブロックを回避して取得する
    instances = [
        "https://rsshub.app",
        "https://rsshub.rssforever.com",
        "https://rsshub.ktachibana.party",
        "https://rsshub.lipten.link"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for instance in instances:
        url = f"{instance}/youtube/channel/{channel_id}"
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                print(f"  [Info] Fetched successfully from: {instance}")
                return response.content
        except Exception as e:
            print(f"  [Info] Failed with {instance}: {e}")
        time.sleep(1)
        
    return None

def process_channel(channel_name, channel_id, output_file):
    content = fetch_xml(channel_id)
    if not content:
        print(f"Skipped: All fetch attempts failed for {channel_name}")
        return False

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        return False
        
    # Feeder向けに、出力用のAtomフィードを新規構築
    ET.register_namespace('', 'http://www.w3.org/2005/Atom')
    feed = ET.Element('{http://www.w3.org/2005/Atom}feed')
    
    title_elem = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}title')
    title_elem.text = channel_name
    
    # RSSHubのデフォルト出力である RSS 2.0 形式の <item> を処理
    for item in root.findall('.//item'):
        entry = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}entry')
        
        title = ET.SubElement(entry, '{http://www.w3.org/2005/Atom}title')
        item_title = item.find('title')
        title.text = item_title.text if item_title is not None else ""
        
        link = ET.SubElement(entry, '{http://www.w3.org/2005/Atom}link')
        item_link = item.find('link')
        link_href = item_link.text if item_link is not None else ""
        link.set('href', link_href)
        
        entry_id = ET.SubElement(entry, '{http://www.w3.org/2005/Atom}id')
        entry_id.text = link_href
        
        updated = ET.SubElement(entry, '{http://www.w3.org/2005/Atom}updated')
        item_pubDate = item.find('pubDate')
        if item_pubDate is not None and item_pubDate.text:
            try:
                dt = parsedate_to_datetime(item_pubDate.text)
                updated.text = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                updated.text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            updated.text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # リンクからビデオIDを抽出
        video_id = ""
        if "watch?v=" in link_href:
            parsed_url = urllib.parse.urlparse(link_href)
            qs = urllib.parse.parse_qs(parsed_url.query)
            video_id = qs.get("v", [""])[0]
        
        # HTML本文作成 (Feederエラーの原因となる埋め込みプレイヤーを完全に排除)
        content_elem = ET.Element('{http://www.w3.org/2005/Atom}content')
        content_elem.set('type', 'html')
        
        # ただ純粋にサムネイル画像のURLを生成し、imgタグだけで表示させる
        if video_id:
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            content_elem.text = f'<img src="{thumbnail_url}" alt="thumbnail">'
        else:
            content_elem.text = "No Image"
            
        entry.append(content_elem)
        
    tree = ET.ElementTree(feed)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    return True

def main():
    channels = [
        {
            "name": "櫻坂46 OFFICIAL YouTube CHANNEL",
            "channel_id": "UCmr9bYmymcBmQ1p2tLBRvwg",
            "output_file": "youtube_official_rss.xml"
        },
        {
            "name": "櫻坂チャンネル",
            "channel_id": "UCDNDlqJRz4FsO_ByfUNOSuQ",
            "output_file": "youtube_sakurazaka_channel_rss.xml"
        }
    ]
    
    for ch in channels:
        print(f"Processing {ch['name']}...")
        success = process_channel(ch["name"], ch["channel_id"], ch["output_file"])
        if success:
            print(f"Success: {ch['name']} -> {ch['output_file']}")
        time.sleep(2)

if __name__ == "__main__":
    main()
