import subprocess
import sys
import time
from datetime import datetime, timezone
from email.utils import formatdate

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
        'extract_flat': True, # Botブロック回避のため、詳細ページまで潜らない軽量モード
        'playlist_end': 5,    # 既存の投稿は最新5件のみに制限
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

    rss_xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">',
        '  <channel>',
        f'    <title>{channel_name}</title>',
        f'    <link>https://www.youtube.com/channel/{channel_id}</link>',
        '    <description>YouTube Feed for Feeder</description>'
    ]
    
    for entry in unique_entries:
        vid = entry.get('id')
        title_raw = entry.get('title', 'No Title')
        
        title = title_raw.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        title_cdata = title_raw.replace(']]>', ']]&gt;')
        
        url = f"https://www.youtube.com/watch?v={vid}"
        thumbnail_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        
        pub_date = None
        timestamp = entry.get('timestamp')
        upload_date_str = entry.get('upload_date')
        
        if timestamp:
            pub_date = formatdate(timestamp, localtime=False)
        elif upload_date_str and len(upload_date_str) == 8:
            try:
                dt = datetime.strptime(upload_date_str, '%Y%m%d').replace(tzinfo=timezone.utc)
                pub_date = formatdate(dt.timestamp(), localtime=False)
            except ValueError:
                pass
        
        html_content = f'<![CDATA[<a href="{url}"><img src="{thumbnail_url}" alt="thumbnail" style="max-width: 100%;"></a><br><br><h3>{title_cdata}</h3><br><a href="{url}">YouTubeで開く</a>]]>'
        
        rss_xml.append('    <item>')
        rss_xml.append(f'      <title>{title}</title>')
        rss_xml.append(f'      <link>{url}</link>')
        rss_xml.append(f'      <guid isPermaLink="false">yt:video:{vid}</guid>')
        
        if pub_date:
            rss_xml.append(f'      <pubDate>{pub_date}</pubDate>')
            
        rss_xml.append(f'      <description>{html_content}</description>')
        rss_xml.append(f'      <content:encoded>{html_content}</content:encoded>')
        rss_xml.append('    </item>')
        
    rss_xml.append('  </channel>')
    rss_xml.append('</rss>')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(rss_xml))
        
    print(f"Success: {channel_name} -> {output_file}")
    return True

def main():
    channels = [
        {
            "name": "櫻坂46 OFFICIAL YouTube CHANNEL",
            "channel_id": "UCmr9bYmymcBmQ1p2tLBRvwg",
            "playlist_id": "UUmr9bYmymcBmQ1p2tLBRvwg",
            "output_file": "youtube_official_rss.xml"
        },
        {
            "name": "櫻坂チャンネル",
            "channel_id": "UCDNDlqJRz4FsO_ByfUNOSuQ",
            "playlist_id": "UUDNDlqJRz4FsO_ByfUNOSuQ",
            "output_file": "youtube_sakurazaka_channel_rss.xml"
        }
    ]
    
    for ch in channels:
        process_channel(ch["name"], ch["channel_id"], ch["playlist_id"], ch["output_file"])
        time.sleep(1)

if __name__ == "__main__":
    main()
