import requests
import xml.etree.ElementTree as ET
import time

def process_channel(channel_name, playlist_id, output_file):
    # チャンネルIDの先頭「UC」を「UU」に変えると「アップロード動画プレイリスト」のIDになる。
    # プレイリストのRSSフィードは、チャンネルフィードよりもボット制限が緩い。
    url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/xml, text/xml, */*; q=0.01'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        content = response.content
    except requests.exceptions.RequestException as e:
        print(f"Request Error for {url}: {e}")
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
        'media': 'http://search.yahoo.com/mrss/',
        'yt': 'http://www.youtube.com/xml/schemas/2015'
    }
    
    for entry in root.findall('atom:entry', ns):
        video_id_elem = entry.find('yt:videoId', ns)
        if video_id_elem is not None and video_id_elem.text:
            video_id = video_id_elem.text
        else:
            continue
            
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
            "playlist_id": "UUmr9bYmymcBmQ1p2tLBRvwg", 
            "output_file": "youtube_official_rss.xml"
        },
        {
            "name": "櫻坂チャンネル",
            "playlist_id": "UUDNDlqJRz4FsO_ByfUNOSuQ",
            "output_file": "youtube_sakurazaka_channel_rss.xml"
        }
    ]
    
    for ch in channels:
        print(f"Processing {ch['name']}...")
        success = process_channel(ch["name"], ch["playlist_id"], ch["output_file"])
        if success:
            print(f"Success: {ch['name']} -> {ch['output_file']}")
        time.sleep(2)

if __name__ == "__main__":
    main()
