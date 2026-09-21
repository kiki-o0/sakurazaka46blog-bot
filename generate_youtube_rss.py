import requests
import xml.etree.ElementTree as ET

def fetch_xml(channel_id):
    # rss2jsonもYouTubeからブロックされているため、YouTubeの代替サイト（Invidious）のRSSからデータを取得する
    urls = [
        f"https://vid.puffyan.us/feed/channel/{channel_id}",
        f"https://yewtu.be/feed/channel/{channel_id}",
        f"https://invidious.flokinet.to/feed/channel/{channel_id}",
        f"https://invidious.nerdvpn.de/feed/channel/{channel_id}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                print(f"  [Info] Fetched successfully from: {url}")
                return response.content
            else:
                print(f"  [Info] Status {response.status_code} for {url}")
        except Exception as e:
            print(f"  [Info] Error for {url}: {e}")
            
    return None

def process_channel(channel_id, output_file):
    content = fetch_xml(channel_id)
    if not content:
        print(f"Skipped: All fetch attempts failed for channel_id={channel_id}")
        return False
        
    # 名前空間の設定
    ET.register_namespace('', 'http://www.w3.org/2005/Atom')
    ET.register_namespace('yt', 'http://www.youtube.com/xml/schemas/2015')
    ET.register_namespace('media', 'http://search.yahoo.com/mrss/')
    
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        return False
        
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'media': 'http://search.yahoo.com/mrss/',
        'yt': 'http://www.youtube.com/xml/schemas/2015'
    }
    
    for entry in root.findall('atom:entry', ns):
        # ビデオIDを取得
        video_id_elem = entry.find('yt:videoId', ns)
        if video_id_elem is not None and video_id_elem.text:
            video_id = video_id_elem.text
        else:
            entry_id = entry.find('atom:id', ns)
            video_id = entry_id.text.replace('yt:video:', '') if entry_id is not None and entry_id.text else ""
        
        # リンク先を公式YouTubeに強制書き換え
        link = entry.find('atom:link', ns)
        if link is not None:
            link.set('href', f"https://www.youtube.com/watch?v={video_id}")
            
        author = entry.find('atom:author', ns)
        if author is not None:
            uri = author.find('atom:uri', ns)
            if uri is not None:
                uri.text = f"https://www.youtube.com/channel/{channel_id}"
        
        # HTMLコンテンツの作成
        content_elem = ET.Element('{http://www.w3.org/2005/Atom}content')
        content_elem.set('type', 'html')
        
        # 公式の高画質サムネイルURLを直接生成
        thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        html_content = f'<img src="{thumbnail_url}" alt="thumbnail">'
        
        media_group = entry.find('media:group', ns)
        if media_group is not None:
            description = media_group.find('media:description', ns)
            if description is not None and description.text:
                escaped_desc = description.text.replace('\n', '<br>')
                html_content += f'<br><br>{escaped_desc}'
        
        content_elem.text = html_content
        
        existing_content = entry.find('atom:content', ns)
        if existing_content is not None:
            entry.remove(existing_content)
        
        entry.append(content_elem)
    
    tree = ET.ElementTree(root)
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
        success = process_channel(ch["channel_id"], ch["output_file"])
        if success:
            print(f"Success: {ch['name']} -> {ch['output_file']}")

if __name__ == "__main__":
    main()
