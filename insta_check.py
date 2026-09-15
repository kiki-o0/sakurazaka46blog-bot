import os
import json
import requests

# お名前でバッチリ統一されたリスト！
MEMBERS = [
    {"name": "山﨑天", "insta_id": "yamasaki.ten", "webhook_env": "WEBHOOK_TEN"},
    {"name": "谷口愛季", "insta_id": "airi.taniguchi.official", "webhook_env": "WEBHOOK_AIRI"},
    {"name": "井上梨名", "insta_id": "inoue.rina_official", "webhook_env": "WEBHOOK_RINA_I"},
    {"name": "遠藤光莉", "insta_id": "hikari.endo_official", "webhook_env": "WEBHOOK_HIKARI"},
    {"name": "大園玲", "insta_id": "reinazono_official", "webhook_env": "WEBHOOK_REI"},
    {"name": "大沼晶保", "insta_id": "akiho.onuma_official", "webhook_env": "WEBHOOK_AKIHO"},
    {"name": "関有美子", "insta_id": "yumiko.seki_official", "webhook_env": "WEBHOOK_YUMIKO"},
    {"name": "武元唯衣", "insta_id": "yui.takemoto_official", "webhook_env": "WEBHOOK_YUI"},
    {"name": "田村保乃", "insta_id": "hono.tamura_official", "webhook_env": "WEBHOOK_HONO"},
    {"name": "藤吉夏鈴", "insta_id": "karin.fujiyoshi_official", "webhook_env": "WEBHOOK_KARIN"},
    {"name": "松田里奈", "insta_id": "rina.matsuda_official", "webhook_env": "WEBHOOK_RINA_M"},
    {"name": "守屋麗奈", "insta_id": "rena.moriya_official", "webhook_env": "WEBHOOK_RENA"},
    {"name": "石森璃花", "insta_id": "rika.ishimori_official", "webhook_env": "WEBHOOK_RIKA"},
    {"name": "遠藤理子", "insta_id": "riko.endo_official", "webhook_env": "WEBHOOK_RIKO"},
    {"name": "小田倉麗奈", "insta_id": "reina.odakura_official", "webhook_env": "WEBHOOK_REINA_O"},
    {"name": "中嶋優月", "insta_id": "yuzuki.nakajima_official", "webhook_env": "WEBHOOK_YUZUKI"},
    {"name": "村井優", "insta_id": "yu.murai_official", "webhook_env": "WEBHOOK_YU"},
    {"name": "村山美羽", "insta_id": "miu.murayama_official", "webhook_env": "WEBHOOK_MIU"},
    {"name": "小池美波", "insta_id": "minami.koike_official", "webhook_env": "WEBHOOK_MINAMI"},
    {"name": "菅井友香", "insta_id": "yuka.sugai_official", "webhook_env": "WEBHOOK_YUUKA"},
]

HISTORY_FILE = "insta_history.json"

def get_latest_post_ninja(insta_id, cookie_value):
    print(f"👀 {insta_id} を忍者ルートで確認中...")
    # Instagramアプリが裏で使っている公式のデータ通信路
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={insta_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-IG-App-ID": "936619743392459", # インスタ公式のパスポート番号（固定値）
        "Cookie": f"sessionid={cookie_value}"
    }
    
    try:
        # 10秒でスパッと諦める設定（絶対にフリーズさせない！）
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ 警備員に弾かれました（{response.status_code}）")
            return None

        # 抜き取ったデータを解読
        data = response.json()
        edges = data.get("data", {}).get("user", {}).get("edge_owner_to_timeline_media", {}).get("edges", [])
        
        if not edges:
            return None
            
        # 最新の投稿（1件目）のIDを抜き取る
        post = edges[0].get("node", {})
        shortcode = post.get("shortcode")
        
        if not shortcode:
            return None

        # 魔法のURL（ddinstagram）に合体させて返す！
        return {
            "id": shortcode,
            "url": f"https://ddinstagram.com/p/{shortcode}/"
        }
        
    except Exception as e:
        print(f"❌ エラーになっちゃった: {e}")
        return None

def main():
    print("=== インスタ確認スタート ===")
    
    cookie_value = os.environ.get("INSTA_COOKIE")
    if not cookie_value:
        print("❌ 合鍵が見つからないよ！")
        return

    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass

    is_updated = False

    for member in MEMBERS:
        webhook_url = os.environ.get(member["webhook_env"])
        if not webhook_url:
            continue

        latest = get_latest_post_ninja(member["insta_id"], cookie_value)
        if not latest:
            continue

        last_id = history.get(member["insta_id"])
        if last_id != latest["id"]:
            print(f"✨ {member['name']} の新しい投稿を発見！Discordへ送るね！")
            
            # 文字の中にURLを入れるだけで、Discordが勝手に写真カードを展開してくれます
            payload = {
                "username": f"{member['name']} Instagram",
                "content": f"✨ **{member['name']}** がInstagramを更新したよ！\n{latest['url']}"
            }
            requests.post(webhook_url, json=payload, timeout=10)
            history[member["insta_id"]] = latest["id"]
            is_updated = True
        else:
            print(f"➡️ {member['name']} の新しい動きはないみたい")

    if is_updated:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print("💾 記録をセーブしたよ")
        
    print("=== 確認終了 ===")

if __name__ == "__main__":
    main()
