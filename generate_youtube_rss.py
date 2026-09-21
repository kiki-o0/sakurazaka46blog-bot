import subprocess
import sys
import time

def install_yt_dlp():
    # YouTubeのブロックを100%回避する最強ツール「yt-dlp」を自動インストール
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
        'playlist_end': 10, # 最新10件ずつ取得
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('entries', [])
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def process_channel(channel_name, channel_id, output_file):
    print(f"Processing {channel_name}...")
    
    # 通常の動画とショート動画を別々に取得して合体させる（ショート漏れを防止）
    videos = fetch_entries(f"https://www.youtube.com/channel/{channel_id}/videos")
    shorts = fetch_entries(f"https://www.youtube.com/channel/{channel_id}/shorts")
    
    all_entries = videos + shorts
    
    # 重複排除
    seen = set()
    unique_entries = []
    for entry in all_entries:
        vid = entry.get('id')
        if vid and vid not in seen:
            seen.add(vid)
            unique_entries.append(entry)
            
    if not unique_entries:
        print(f"Skipped: Could not fetch any videos for {channel_name}")
        return False

    # Feederで恐竜エラー（iframe化）を防ぐため、リッチなRSS 2.0形式で構築
    rss_xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        '  <channel>',
        f'    <title>{channel_name}</title>',
        f'    <link>https://www.youtube.com/channel/{channel_id}</link>',
        '    <description>YouTube Feed for Feeder</description>'
    ]
    
    for entry in unique_entries:
        vid = entry.get('id')
        title_raw = entry.get('title', 'No Title')
        
        # XML構文エラー防止のエスケープ
        title = title_raw.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        title_cdata = title_raw.replace(']]>', ']]&gt;')
        
        url = f"https://www.youtube.com/watch?v={vid}"
        thumbnail_url = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        
        # CDATAを使用して純粋なHTML記事として認識させる（画像＋タイトル＋リンクテキスト）
        description = f'<![CDATA[<a href="{url}"><img src="{thumbnail_url}" alt="thumbnail" style="max-width: 100%;"></a><br><br><h3>{title_cdata}</h3><br><a href="{url}">YouTubeで開く</a>]]>'
        
        rss_xml.append('    <item>')
        rss_xml.append(f'      <title>{title}</title>')
        rss_xml.append(f'      <link>{url}</link>')
        rss_xml.append(f'      <guid isPermaLink="false">yt:video:{vid}</guid>')
        rss_xml.append(f'      <description>{description}</description>')
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
            "output_file": "youtube_official_rss.xml"
        },
        {
            "name": "櫻坂チャンネル",
            "channel_id": "UCDNDlqJRz4FsO_ByfUNOSuQ",
            "output_file": "youtube_sakurazaka_channel_rss.xml"
        }
    ]
    
    for ch in channels:
        process_channel(ch["name"], ch["channel_id"], ch["output_file"])
        time.sleep(1)

if __name__ == "__main__":
    main()
