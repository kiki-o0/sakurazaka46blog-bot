import os
import json
import requests
import instaloader

# お名前でバッチリ統一された完璧なリストだよ！
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

def get_latest_post_instaloader(insta_id, cookie_value):
    print(f"👀 {insta_id} のページを確認中...")
    try:
        L = instaloader.Instaloader(quiet=True)
        L.context._session.cookies.set('sessionid', cookie_value, domain='.instagram.com')
        
        profile = instaloader.Profile.from_username(L.context, insta_id)
        post = next(profile.get_posts())
        
        return {
            "id": post.shortcode,
            # Instagramの代わりに、Discordが写真を見れる魔法のURL（ddinstagram）に変えるよ！
            "url": f"https://ddinstagram.com/p/{post.shortcode}/"
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

        latest = get_latest_post_instaloader(member["insta_id"], cookie_value)
        if not latest:
            continue

        last_id = history.get(member["insta_id"])
        if last_id != latest["id"]:
            print(f"✨ {member['name']} の新しい投稿を発見！Discordへ送るね！")
            
            # 難しい設定はナシ！魔法のURLを送るだけでDiscordが綺麗なカードを作ってくれるよ！
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
