import os
import re
import json
import time
from datetime import datetime, timezone
from xml.sax.saxutils import escape
import requests

# ==========================================
# 設定部分
# ==========================================
SOURCE_STATE_FILE = "last_blogs.json"
AI_STATE_FILE = "ai_summary_state.json"
FEED_FILENAME = "ai_summary_feed.xml"
FEED_BASE_URL = "https://kiki-o0.github.io/sakurazaka46blog-bot/"
GITHUB_RAW_URLS = [
    "https://raw.githubusercontent.com/kiki-o0/sakurazaka46blog-bot/main/last_blogs.json",
    "https://raw.githubusercontent.com/kiki-o0/sakurazaka46blog-bot/master/last_blogs.json"
]
MAX_API_CALLS_PER_RUN = 10  # 1回の実行で新しくAIに要約させる最大件数
FEED_MAX_ENTRIES = 30       # フィードに表示する最新記事の最大数

# ==========================================
# AIに渡す最強のメンバー辞書＆ルール
# ==========================================
MEMBER_DICTIONARY = """
【1期生】
上村 莉菜 (うえむー) / 小池 美波 (みいちゃん) / 齋藤 冬優花 (ふーちゃん)
【2期生】
井上 梨名 (いのり, いのりちゃん) / 遠藤 光莉 (えんぴか, ひかりん) / 大園 玲 (玲ちゃん, ぞの)
大沼 晶保 (あきぽ, 沼ちゃん) / 幸阪 茉里乃 (まりの, まりのん) / 武元 唯衣 (ちゅけ, ちゅけもん)
田村 保乃 (ほのす, ほのちゃん) / 藤吉 夏鈴 (かりん, かりんちゃん) / 増本 綺良 (きらこ, きらちゃん)
松田 里奈 (まつり, まっちゃん) / 森田 ひかる (るんちゃん, るんるん) / 守屋 麗奈 (れなぁ) / 山﨑 天 (天ちゃん)
【3期生】
石森 璃花 (りか, りかちゃん) / 遠藤 理子 (えんりこ, りー) / 小田倉 麗奈 (お嬢, れいな)
小島 凪紗 (こんなぎ, なぎ) / 谷口 愛季 (あいり) / 中嶋 優月 (ゆーづ)
的に 美青 (みお) / 向井 純葉 (いとは, いとちゃん) / 村井 優 (ゆう, ゆうちゃん)
村山 美羽 (みう) / 山下 瞳月 (しーちゃん,しー)
【4期生】
浅井 恋乃未 (このみ, このみん) / 稲熊 ひな (ひなぐま) / 勝又 春 (ﾊﾙｻﾝ)
佐藤 愛桜 (ねお, ねおちゃん) / 中川 智尋 (ちー,ちーたん) / 松本 和子 (わこち)
目黒 陽色 / 山川 宇衣 (ういえる,ういたん) / 山田 桃実 (ももちゃん,ももみん)
"""

AI_SYSTEM_PROMPT = f"""
あなたは櫻坂46の事情通であり、優秀な要約アシスタントです。
渡されたブログの「筆者」と「本文」を読み、以下のJSON形式で絶対に出力してください。
Markdownのバッククォート(```jsonなど)は含めず、純粋なJSONテキストのみを返してください。

{{
  "summary": ["要約1行目", "要約2行目", "要約3行目"],
  "tags": ["#メンバー名1", "#メンバー名2"]
}}

【タグ付けの厳格なルール】
1. 以下の「メンバー辞書」に存在するフルネーム、または()内の愛称が本文にある場合のみタグ付けしてください。
2. 当てずっぽうの推測は厳禁です。
3. 特別ルール: 本文に「麗奈」とだけあり、筆者が3期生の場合は先輩(守屋)を呼び捨てにしないため「#小田倉麗奈」と判定してください。

【メンバー辞書】
{MEMBER_DICTIONARY}
"""

def load_source_state():
    if os.path.exists(SOURCE_STATE_FILE):
        print(f"-> [読込中] ローカルの {SOURCE_STATE_FILE} を確認しました")
        try:
            with open(SOURCE_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"  -> [警告] ローカルファイルの読み込み失敗: {e}")

    print("-> [RSS取得中] GitHubから最新ブログデータを取得しています...")
    for url in GITHUB_RAW_URLS:
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                print("  -> [成功] GitHubから最新ブログデータの取得が完了しました")
                return res.json()
        except Exception as e:
            print(f"  -> [スキップ] 取得失敗 ({url}): {e}")

    return None

def get_ai_summary(api_key, author, text):
    api_url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=){api_key}"
    full_prompt = f"{AI_SYSTEM_PROMPT}\n\n【筆者】\n{author}\n\n【本文】\n{text}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": full_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        res = requests.post(api_url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        res_data = res.json()
        
        raw_output = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]
        if raw_output.startswith("```"):
            raw_output = raw_output[3:]
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]
            
        return json.loads(raw_output.strip())
    except Exception as e:
        print(f"  -> [AI解析エラー] Geminiとの通信・解析に失敗しました: {e}")
        return None

def main():
    print("=== [処理開始] AI要約フィードの生成処理を開始します ===")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[エラー] 環境変数 GEMINI_API_KEY が設定されていません。処理を中断します。")
        return

    source_state = load_source_state()
    if not source_state:
        print("[エラー] ブログデータの取得に失敗しました。処理を終了します。")
        return

    ai_state = {}
    if os.path.exists(AI_STATE_FILE):
        try:
            with open(AI_STATE_FILE, "r", encoding="utf-8") as f:
                ai_state = json.load(f)
        except Exception:
            pass

    all_articles = []
    for member_id, articles in source_state.items():
        if isinstance(articles, list):
            for article in articles:
                article["member_id"] = member_id
                all_articles.append(article)
                
    all_articles.sort(key=lambda x: x.get("updated", ""), reverse=True)
    
    api_call_count = 0
    feed_entries = []
    
    for article in all_articles[:FEED_MAX_ENTRIES]:
        url = article.get("url", "")
        if not url:
            continue
            
        if url in ai_state:
            feed_entries.append(ai_state[url])
            continue
            
        if api_call_count >= MAX_API_CALLS_PER_RUN:
            print(f"[新着判定中] 1回の実行上限({MAX_API_CALLS_PER_RUN}件)に達したため、残りは次回処理します")
            break
            
        print(f"[AI解析中] 『{article.get('title', '無題')}』の要約とタグを生成しています...")
        
        raw_text = re.sub(r'<[^>]+>', '', article.get("content", "")).strip()
        raw_text = raw_text[:2000] 
        
        author_hint = f"メンバーID: {article.get('member_id', '不明')} (※3期生は60番台が中心です)"
        
        ai_result = get_ai_summary(api_key, author_hint, raw_text)
        if ai_result:
            api_call_count += 1
            
            summary_text = chr(10).join([f"・{line}" for line in ai_result.get("summary", [])])
            tags_text = " ".join(ai_result.get("tags", []))
            
            rich_content = f"""
<div style="background-color: #f7f9f9; padding: 10px; margin-bottom: 15px; border-radius: 5px;">
    <p><strong>💡 AI 3行ハイライト</strong></p>
    <p style="margin-top: 5px; font-size: 0.95em;">{escape(summary_text).replace(chr(10), '<br>')}</p>
</div>
{article.get('content', '')}
"""
            display_title = article.get("title", "無題")
            if tags_text:
                display_title += f" [{tags_text}]"
                
            summarized_article = {
                "url": url,
                "title": display_title,
                "updated": article.get("updated", ""),
                "content": rich_content
            }
            
            ai_state[url] = summarized_article
            feed_entries.append(summarized_article)
            
            print(f"  -> [解析成功] 抽出タグ: {tags_text}")
            time.sleep(2)

    if not feed_entries:
        print("[完了] 出力する記事がありませんでした。")
        return
        
    feed_updated = feed_entries[0].get("updated", datetime.now(timezone.utc).isoformat())
    feed_url = f"{FEED_BASE_URL}{FEED_FILENAME}"
    
    entries_xml = ""
    for entry in feed_entries:
        entries_xml += f"""
  <entry>
    <title>{escape(entry['title'])}</title>
    <id>{escape(entry['url'])}</id>
    <link href="{escape(entry['url'])}"/>
    <updated>{escape(entry['updated'])}</updated>
    <content type="html"><![CDATA[
{entry['content']}
    ]]></content>
  </entry>"""
        
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>櫻坂46｜AI要約＆タグ付き 新着まとめ</title>
  <id>{escape(feed_url)}</id>
  <updated>{escape(feed_updated)}</updated>
  <link href="{escape(feed_url)}" rel="self"/>{entries_xml}
</feed>
"""
    os.makedirs("feeds", exist_ok=True)
    with open(f"feeds/{FEED_FILENAME}", "w", encoding="utf-8") as f:
        f.write(xml)
        
    with open(AI_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(ai_state, f, ensure_ascii=False, indent=2)
        
    print(f"=== [処理完了] AI要約フィードを作成しました (feeds/{FEED_FILENAME}) ===")

if __name__ == "__main__":
    main()
