import os
import re
import time
import json
from datetime import datetime, timezone
from urllib.parse import urljoin
from xml.sax.saxutils import escape

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://sakurazaka46.com"
FEED_BASE_URL = "https://kiki-o0.github.io/sakurazaka46blog-bot/"
STATE_FILE = "last_blogs.json"

MEMBER_MAPPING = {
    # 2期生
    "46": "田村 保乃", "47": "藤吉 夏鈴", "48": "松田 里奈", "50": "森田 ひかる", "51": "山﨑 天",
    # 新2期生
    "53": "遠藤 光莉", "54": "大園 玲", "55": "大沼 晶保", "56": "幸阪 茉里乃", "57": "増本 綺良", "58": "守屋 麗奈",
    # 3期生
    "59": "石森 璃花", "60": "遠藤 理子", "61": "小田倉 麗奈", "62": "小島 凪紗", "63": "谷口 愛季", 
    "64": "中嶋 優月", "65": "的野 美青", "66": "向井 純葉", "67": "村井 優", "68": "村山 美羽", "69": "山下 瞳月",
    # 4期生
    "70": "浅井 恋乃未", "71": "稲熊 ひな", "72": "勝又 春", "73": "佐藤 愛桜", "74": "中川 智尋", 
    "75": "松本 和子", "76": "目黒 陽色", "77": "山川 宇衣", "78": "山田 桃実"
}

def parse_date_to_iso(date_str):
    m = re.findall(r'\d+', date_str)
    if len(m) >= 3:
        year, month, day = m[0], m[1], m[2]
        hour = m[3] if len(m) >= 4 else "00"
        minute = m[4] if len(m) >= 5 else "00"
        second = m[5] if len(m) >= 6 else "00"
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}T{hour.zfill(2)}:{minute.zfill(2)}:{second.zfill(2)}+09:00"
    return datetime.now(timezone.utc).isoformat()

def parse_article(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    detailed_date = ""
    date_tags = soup.find_all(class_="date")
    for tag in date_tags:
        text = tag.get_text(strip=True)
        if re.search(r'\d{1,2}:\d{2}', text):
            detailed_date = text
            break
            
    article = soup.find(class_="box-article")
    if not article:
        return "", detailed_date
        
    for guide in article.find_all(class_=lambda x: x and 'app_guide' in x):
        guide.decompose()
        
    for img in article.find_all("img"):
        src = img.get("src", "")
        if not src or "app_guide" in src:
            img.decompose()
            continue
            
        img_url = urljoin(BASE_URL, src)
        safe_url = escape(img_url)
        img_html = f'<p><a href="{safe_url}"><img src="{safe_url}" alt=""></a></p>'
        img.replace_with(f"__IMG_START__{img_html}__IMG_END__")
        
    elements = []
    raw_text = article.get_text(separator="\n", strip=True)
    parts = re.split(r'__IMG_START__(.*?)__IMG_END__', raw_text)
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
            
        if i % 2 == 1:
            elements.append(part)
        else:
            for line in part.split("\n"):
                line = line.strip()
                if "からのメッセージを受け取る" in line or line == "櫻坂46メッセージ" or line == "「櫻坂46メッセージ」で":
                    continue
                if line:
                    safe_line = escape(line)
                    linked_line = re.sub(r'(https?://[a-zA-Z0-9./?=_-]+)', r'<a href="\1" target="_blank">\1</a>', safe_line)
                    elements.append("<p>" + linked_line + "</p>")
                    
    return chr(10).join(elements), detailed_date

def generate_feed_for_member(member_id, state):
    member_name = MEMBER_MAPPING.get(member_id, f"メンバー{member_id}")
    safe_member_name = member_name.replace(" ", "").replace("　", "")
    
    # 過去の履歴（JSON）から、このメンバーの知っているURLリストを作成
    member_state = state.get(member_id, [])
    # 古い形式の記憶ファイル（文字だけ）が残っていたら、空の状態にリセットする処理を追加
    if not isinstance(member_state, list):
        print(f"[{member_id}] [警告] 古い形式の記憶を見つけたため、新しく作り直します。")
        member_state = []
        
    known_urls = { entry["url"]: entry for entry in member_state if isinstance(entry, dict) and "url" in entry }
    
    list_url = f"{BASE_URL}/s/s46/diary/blog/list?ct={member_id}"
    print(f"[{member_id}] [RSS取得中] {member_name} のブログ一覧にアクセスしています...")
    try:
        res = requests.get(list_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"[{member_id}] [エラー] リスト取得失敗: {e}")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    posts = soup.find_all("li", class_="box")
    if not posts:
        print(f"[{member_id}] [スキップ] {member_name} の新着記事が見つかりません")
        return
        
    new_member_state = []
    feed_updated = None
    
    print(f"[{member_id}] [解析中] {member_name} の記事を処理します（最大15件）")
    
    for post in posts:
        if len(new_member_state) >= 15:
            break
            
        post_a = post.find("a")
        if not post_a:
            continue
            
        href = post_a.get("href", "")
        if "/diary/detail/" not in href:
            continue
            
        title_tag = post.find(class_="title")
        title = title_tag.text.strip() if title_tag and title_tag.text.strip() else "無題"
            
        post_name_tag = post.find(class_="name")
        if post_name_tag:
            post_author = post_name_tag.text.strip()
            safe_post_author = post_author.replace(" ", "").replace("　", "")
            if not safe_member_name.startswith("メンバー") and safe_post_author != safe_member_name:
                print(f"  -> [除外] 他メンバー（{post_author}）の記事を検知: スキップします")
                continue
                
        article_url = urljoin(BASE_URL, href)
        
        if article_url in known_urls:
            print(f"  -> [高速スキップ] 既知の記事です（データ復元）: {title}")
            known_data = known_urls[article_url]
            new_member_state.append(known_data)
            if not feed_updated:
                feed_updated = known_data["updated"]
            continue
        
        print(f"  -> [新規取得中] 記事タイトル: {title}")
        try:
            content, detailed_date = parse_article(article_url)
            print(f"     => [成功] 記事解析完了")
        except Exception as e:
            print(f"     => [エラー] 記事解析失敗 ({article_url}): {e}")
            continue
            
        time.sleep(1)
        
        if not detailed_date:
            date_tag = post.find(class_="date")
            detailed_date = date_tag.text.strip() if date_tag else ""
            
        entry_updated = parse_date_to_iso(detailed_date)
        if not feed_updated:
            feed_updated = entry_updated
            
        new_member_state.append({
            "url": article_url,
            "title": title,
            "updated": entry_updated,
            "content": content
        })

    if not new_member_state:
        print(f"[{member_id}] [スキップ] {member_name} の有効なブログ記事はありませんでした")
        return
        
    if not feed_updated:
        feed_updated = datetime.now(timezone.utc).isoformat()
        
    entries_xml = ""
    for entry_data in new_member_state:
        entries_xml += f"""
  <entry>
    <title>{escape(entry_data['title'])}</title>
    <id>{escape(entry_data['url'])}</id>
    <link href="{escape(entry_data['url'])}"/>
    <updated>{escape(entry_data['updated'])}</updated>
    <author>
      <name>{escape(member_name)}</name>
    </author>
    <content type="html"><![CDATA[
{entry_data['content']}
    ]]></content>
  </entry>"""
        
    feed_filename = f"feed_{member_id}.xml"
    feed_url = f"{FEED_BASE_URL}{feed_filename}"
    
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>櫻坂46｜{escape(member_name)} 公式ブログ</title>
  <id>{escape(feed_url)}</id>
  <updated>{escape(feed_updated)}</updated>
  <link href="{escape(feed_url)}" rel="self"/>{entries_xml}
</feed>
"""
    with open(f"feeds/{feed_filename}", "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"[{member_id}] [完了] {member_name} のフィード生成 (feeds/{feed_filename})")
    
    state[member_id] = new_member_state

def main():
    print("=== [処理開始] 全メンバーのRSS生成を開始します ===")
    os.makedirs("feeds", exist_ok=True)
    
    if os.path.exists(STATE_FILE):
        print("-> [読込] 過去のブログ履歴データを読み込みます...")
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception as e:
            print(f"-> [警告] 履歴ファイルの読み込みに失敗しました。新規で作成します: {e}")
            state = {}
    else:
        print("-> [読込] 過去の履歴がありません。新規で全取得します。")
        state = {}

    for member_id in MEMBER_MAPPING.keys():
        generate_feed_for_member(member_id, state)
        time.sleep(1)
        
    print(f"=== [保存] ブログ履歴データを {STATE_FILE} に保存します ===")
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"-> [エラー] 履歴ファイルの保存に失敗しました: {e}")
        
    print("=== [処理完了] 全てのRSS生成が正常に終了しました ===")

if __name__ == "__main__":
    main()
