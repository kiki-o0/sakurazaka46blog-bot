import requests
import xml.etree.ElementTree as ET
import urllib.parse

def process_channel(url, output_file):
    # GitHub ActionsのIP制限による404エラーを回避するため、プロキシAPIを経由する
    encoded_url = urllib.parse.quote(url)
    proxy_url = f"https://api.allorigins.win/raw?url={encoded_url}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(proxy_url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"Skipped: Status {response.status_code} - {url}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return False
    
    ET.register_namespace('', 'http://www.w3.org/2005/Atom')
    ET.register_namespace('yt', 'http://www.youtube.com/xml/schemas/2015')
    ET.register_namespace('media', 'http://search.yahoo.com/mrss/')
    
    try:
        root = ET.fromstring(response.content)
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
                
                content = ET.Element('{http://www.w3.org/2005/Atom}content')
                content.set('type', 'html')
                
                html_content = f'<img src="{thumbnail_url}" alt="thumbnail">'
                
                description = media_group.find('media:description', ns)
                if description is not None and description.text:
                    escaped_desc = description.text.replace('\n', '<br>')
                    html_content += f'<br><br>{escaped_desc}'
                
                content.text = html_content
                
                existing_content = entry.find('atom:content', ns)
                if existing_content is not None:
                    entry.remove(existing_content)
                
                entry.append(content)
    
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
