import subprocess
import sys
import time
from datetime import datetime
import xml.etree.ElementTree as ET

def install_yt_dlp():
    try:
        import yt_dlp
    except ImportError:
        print("Installing yt-dlp...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])

install_yt_dlp()
import yt_dlp

def fetch_entries(url):
    ydl_opts = {
        'extract_flat': True,
        'playlist_end': 15,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info and 'entries' in info:
                return info['entries']
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return []

def process_channel(channel_name, channel_id, playlist_id, output_file):
    print(f"Processing {channel_name}...")
    
    # ショート動画を含め安定して取得できる「アップロード動画プレイリスト」と「ショート専用URL」の両方を取得して合体
    videos = fetch_entries(f"https://www.youtube.com/playlist?list={playlist_id}")
    shorts = fetch_entries(f"https://www.youtube.com/channel/{channel_id}/shorts")
    
    all_entries = videos + shorts
    
    seen = set()
    unique_entries = []
    for entry in all_entries:
        if not entry:
            continue
        vid = entry.get('id')
        if vid and vid not in seen:
            seen.add(vid)
            unique_entries.append(entry)
            
    if not unique_entries:
        print(f"Skipped: Could not fetch any videos for {channel_name}")
        return False

    # Feederが赤丸ボタン（手動取得）なしで本文を認識できるよう、ブログと同じAtom形式で生成
    ET.register_namespace('', 'http://www.w3.org/2005/Atom')
    feed = ET.Element('{http://www.w3.org/2005/Atom}feed')
    
    title_elem = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}title')
    title_elem.text = channel_name
    
    link_elem = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}link')
    link_elem.set('href', f"https://www.youtube.com/channel/{channel_id}")
    
    updated_elem = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}updated')
    updated_elem.text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    id_elem = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}id')
    id_elem.text = f"yt:channel:{channel_id}"

    for entry in unique_entries:
        vid = entry.get('id')
        title_raw = entry.get('title', 'No Title')
        url = f"https://www.youtube.com/watch?v={vid}"
        thumbnail_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        
        entry_elem = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}entry')
        
        e_title = ET.SubElement(entry_elem, '{http://www.w3.org/2005/Atom}title')
        e_title.text = title_raw
        
        e_link = ET.SubElement(entry_elem, '{http://www.w3.org/2005/Atom}link')
        e_link.set('href', url)
        
        e_id = ET.SubElement(entry_elem, '{http://www.w3.org/2005/Atom}id')
        e_id.text = f"yt:video:{vid}"
        
        e_updated = ET.SubElement(entry_elem, '{http://www.w3.org/2005/Atom}updated')
        e_updated.text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # contentタグ（type="html"）を使用することでFeederの内部ブラウザ起動を回避
        e_content = ET.SubElement(entry_elem, '{http://www.w3.org/2005/Atom}content')
        e_content.set('type', 'html')
        
        html_content = f'<a href="{url}"><img src="{thumbnail_url}" alt="thumbnail" style="max-width: 100%;"></a><br><br><h3>{title_raw}</h3><br><a href="{url}">YouTubeで開く</a>'
        e_content.text = html_content
        
    tree = ET.ElementTree(feed)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
    print(f"Success: {channel_name} -> {output_file}")
    return True

def main():
    channels = [
        {
            "name": "櫻坂46 OFFICIAL YouTube CHANNEL",
            "channel_id": "UCmr9bYmymcBmQ1p2tLBRvwg",
            "playlist_id": "UUmr9bYmymcBmQ1p2tLBRvwg", # アップロード動画プレイリスト
            "output_file": "youtube_official_rss.xml"
        },
        {
            "name": "櫻坂チャンネル",
            "channel_id": "UCDNDlqJRz4FsO_ByfUNOSuQ",
            "playlist_id": "UUDNDlqJRz4FsO_ByfUNOSuQ", # アップロード動画プレイリスト
            "output_file": "youtube_sakurazaka_channel_rss.xml"
        }
    ]
    
    for ch in channels:
        process_channel(ch["name"], ch["channel_id"], ch["playlist_id"], ch["output_file"])
        time.sleep(1)

if __name__ == "__main__":
    main()
