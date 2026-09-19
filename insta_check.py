import requests
import xml.etree.ElementTree as ET


ATOM_NS = "http://www.w3.org/2005/Atom"


RSS_URL = (
    "https://rss-bridge.org/bridge01/"
    "?action=display"
    "&bridge=InstagramBridge"
    "&context=Username"
    "&u={username}"
    "&media_type=all"
    "&format=Atom"
)


def fetch_raw_response(username):
    url = RSS_URL.format(username=username)
    
    print(f"=== {username} のRSS取得 ===")
    print(f"URL: {url}")
    
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=40,
    )
    
    print(f"HTTPステータス: {response.status_code}")
    print(f"レスポンスサイズ: {len(response.content)} バイト")
    print(f"レスポンス全体:")
    print(response.text)
    print("=" * 60)
    
    return response.text


def parse_and_compare(xml_text_1, xml_text_2, user1, user2):
    print("
=== 構造化データ比較 ===
")
    
    try:
        root1 = ET.fromstring(xml_text_1.encode("utf-8"))
        root2 = ET.fromstring(xml_text_2.encode("utf-8"))
    except ET.ParseError as e:
        print(f"XML解析エラー: {e}")
        return
    
    entry_tag = "{" + ATOM_NS + "}entry"
    entries1 = root1.findall(entry_tag)
    entries2 = root2.findall(entry_tag)
    
    print(f"{user1} のエントリー数: {len(entries1)}")
    print(f"{user2} のエントリー数: {len(entries2)}")
    
    if len(entries1) == 0 and len(entries2) > 0:
        print(f"
→ {user2} だけがエントリーを取得できている！")
        print(f"→ {user1} のRSS-Bridgeが機能していない")
    
    if len(entries1) > 0:
        print(f"
{user1} のエントリー詳細:")
        for i, entry in enumerate(entries1[:3], 1):
            title = entry.find(f"{{{ATOM_NS}}}title")
            published = entry.find(f"{{{ATOM_NS}}}published")
            link = entry.find(f"{{{ATOM_NS}}}link")
            entry_id = entry.find(f"{{{ATOM_NS}}}id")
            
            print(f"  [{i}]")
            print(f"      ID: {entry_id.text if entry_id is not None else 'N/A'}")
            print(f"      タイトル: {title.text if title is not None else 'N/A'}")
            print(f"      公開日: {published.text if published is not None else 'N/A'}")
            print(f"      リンク: {link.attrib.get('href', 'N/A') if link is not None else 'N/A'}")
    
    if len(entries2) > 0:
        print(f"
{user2} のエントリー詳細:")
        for i, entry in enumerate(entries2[:3], 1):
            title = entry.find(f"{{{ATOM_NS}}}title")
            published = entry.find(f"{{{ATOM_NS}}}published")
            link = entry.find(f"{{{ATOM_NS}}}link")
            entry_id = entry.find(f"{{{ATOM_NS}}}id")
            
            print(f"  [{i}]")
            print(f"      ID: {entry_id.text if entry_id is not None else 'N/A'}")
            print(f"      タイトル: {title.text if title is not None else 'N/A'}")
            print(f"      公開日: {published.text if published is not None else 'N/A'}")
            print(f"      リンク: {link.attrib.get('href', 'N/A') if link is not None else 'N/A'}")


def main():
    print("=== Instagram RSS-Bridge 詳細比較 ===
")
    
    user1 = "yamasaki.ten"
    user2 = "airi.taniguchi.official"
    
    xml1 = fetch_raw_response(user1)
    xml2 = fetch_raw_response(user2)
    
    parse_and_compare(xml1, xml2, user1, user2)
    
    print("
=== 考察 ===")
    print("両者のRSSレスポンスを比較して、以下の点を確認:")
    print("1. エントリー数の違い")
    print("2. XML構造の違い")
    print("3. エラーメッセージの有無")
    print("4. 更新日時（updated）の違い")


if __name__ == "__main__":
    main()
