import requests
import xml.etree.ElementTree as ET

def process_channel(url, output_file):
    # RSSの取得（YouTubeのボット対策による404エラーを回避するためUser-Agentを指定）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # XMLのパース
    # 名前空間の登録（出力時に接頭辞がns0などにならないようにする）
    ET.register_namespace('', 'http://www.w3.org/2005/Atom')
    ET.register_namespace('yt', 'http://www.youtube.com/xml/schemas/2015')
    ET.register_namespace('media', 'http://search.yahoo.com/mrss/')
    
    root = ET.fromstring(response.content)
    
    # 検索用のXML名前空間の設定
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'media': 'http://search.yahoo.com/mrss/'
    }
    
    # 各投稿（entry）を処理
    for entry in root.findall('atom:entry', ns):
        # media:group内のmedia:thumbnailを取得
        media_group = entry.find('media:group', ns)
        if media_group is not None:
            thumbnail = media_group.find('media:thumbnail', ns)
            if thumbnail is not None:
                thumbnail_url = thumbnail.get('url')
                
                # 新しいcontent要素を作成（HTMLとして画像を埋め込む）
                content = ET.Element('{http://www.w3.org/2005/Atom}content')
                content.set('type', 'html')
                
                # サムネイル画像のimgタグを作成
                html_content = f'<img src="{thumbnail_url}" alt="thumbnail">'
                
                # 概要（description）があれば画像の後にテキストとして追加
                description = media_group.find('media:description', ns)
                if description is not None and description.text:
                    # 改行を<br>に変換
                    escaped_desc = description.text.replace('\n', '<br>')
                    html_content += f'<br><br>{escaped_desc}'
                
                content.text = html_content
                
                # 既存のcontent要素があれば削除（重複防止）
                existing_content = entry.find('atom:content', ns)
                if existing_content is not None:
                    entry.remove(existing_content)
                
                # 新しく作成したcontent要素を追加
                entry.append(content)
    
    # 変換したXMLをファイルとして保存
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

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
        try:
            process_channel(ch["url"], ch["output_file"])
            print(f"Success: {ch['name']} -> {ch['output_file']}")
        except Exception as e:
            print(f"Error processing {ch['name']}: {e}")

if __name__ == "__main__":
    main()
