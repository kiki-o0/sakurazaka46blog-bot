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
    
    print("=== " + username + " のRSS取得 ===")
    print("URL: " + url)
    
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=40,
    )
    
    print("HTTPステータス: " + str(response.status_code))
    print("レスポンスサイズ: " + str(len(response.content)) + " バイト")
    print("レスポンス全体:")
    print(response.text)
    print("=" * 60)
    
    return response.text


def parse_and_compare(xml_text_1, xml_text_2, user1, user2):
    print("")
    print("=== 構造化データ比較 ===")
    print("")
    
    try:
        root1 = ET.fromstring(xml_text_1.encode("utf-8"))
        root2 = ET.fromstring(xml_text_2.encode("utf-8"))
    except ET.ParseError as e:
        print("XML解析エラー: " + str(e))
        return
    
    entry_tag = "{" + ATOM_NS + "}entry"
    entries1 = root1.findall(entry_tag)
    entries2 = root2.findall(entry_tag)
    
    print(user1 + " のエントリー数: " + str(len(entries1)))
    print(user2 + " のエントリー数: " + str(len(entries2)))
    
    if len(entries1) == 0 and len(entries2) > 0:
        print("")
        print(user2 + " だけがエントリーを取得できている！")
        print(user1 + " のRSS-Bridgeが機能していない")
    
    if len(entries1) > 0:
        print("")
        print(user1 + " のエントリー詳細:")
        for i, entry in enumerate(entries1[:3], 1):
            title = entry.find("{" + ATOM_NS + "}title")
            published = entry.find("{" + ATOM_NS + "}published")
            link = entry.find("{" + ATOM_NS + "}link")
            entry_id = entry.find("{" + ATOM_NS + "}id")
            
            print("  [" + str(i) + "]")
            print("      ID: " + (entry_id.text if entry_id is not None else "N/A"))
            print("      タイトル: " + (title.text if title is not None else "N/A"))
            print("      公開日: " + (published.text if published is not None else "N/A"))
            print("      リンク: " + (link.attrib.get("href", "N/A") if link is not None else "N/A"))
    
    if len(entries2) > 0:
        print("")
        print(user2 + " のエントリー詳細:")
        for i, entry in enumerate(entries2[:3], 1):
            title = entry.find("{" + ATOM_NS + "}title")
            published = entry.find("{" + ATOM_NS + "}published")
            link = entry.find("{" + ATOM_NS + "}link")
            entry_id = entry.find("{" + ATOM_NS + "}id")
            
            print("  [" + str(i) + "]")
            print("      ID: " + (entry_id.text if entry_id is not None else "N/A"))
            print("      タイトル: " + (title.text if title is not None else "N/A"))
            print("      公開日: " + (published.text if published is not None else "N/A"))
            print("      リンク: " + (link.attrib.get("href", "N/A") if link is not None else "N/A"))


def main():
    print("=== Instagram RSS-Bridge 詳細比較 ===")
    print("")
    
    user1 = "yamasaki.ten"
    user2 = "airi.taniguchi.official"
    
    xml1 = fetch_raw_response(user1)
    xml2 = fetch_raw_response(user2)
    
    parse_and_compare(xml1, xml2, user1, user2)
    
    print("")
    print("=== 考察 ===")
    print("両者のRSSレスポンスを比較して、以下の点を確認:")
    print("1. エントリー数の違い")
    print("2. XML構造の違い")
    print("3. エラーメッセージの有無")
    print("4. 更新日時（updated）の違い")


if __name__ == "__main__":
    main()
