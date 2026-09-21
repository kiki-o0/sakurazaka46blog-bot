import requests
import xml.etree.ElementTree as ET
import urllib.parse
import time

def fetch_xml(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/xml, text/xml, */*; q=0.01'
    }
    
    encoded_url_all = urllib.parse.quote(url, safe='')
    
    # 直接アクセスと、複数の異なるプロキシを順番に試行するリスト
    urls_to_try = [
        url,
        f"https://api.codetabs.com/v1/proxy?quest={url}",
        f"https://corsproxy.io/?{encoded_url_all}"
    ]
    
    for try_url in urls_to_try:
        try:
            response = requests.get(try_url, headers=headers, timeout=20)
            if response.status_code == 200:
                # 正常にXMLが取得できた場合は内容を返す
                return response.content
            else:
                print(f"  [Info] Failed to fetch with {try_url} (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"  [Info] Request Error with {try_url}: {e}")
        
        # 次のアクセス先を試す前に少し待機
        time.sleep(2)
        
    return None

def process_channel(url, output_file):
    content = fetch_xml(url)
    if not content:
        print(f"Skipped: All fetch attempts failed for {url}")
        return False
        
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
        'media': 'http://search.yahoo.com/mrss/'
    }
    
    for entry in root.findall('atom:entry', ns):
        media_group = entry.find('media:group', ns)
        if media_group is not None:
            thumbnail = media_group.find('media:thumbnail', ns)
            if thumbnail is not None:
                thumbnail_url = thumbnail.get('url')
                
                content_elem = ET.Element('{http://www.w3.org/2005/Atom}content')
                content_elem.set('type', 'html')
                
                html_content = f'<img src="{thumbnail_url}" alt="thumbnail">'
                
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
