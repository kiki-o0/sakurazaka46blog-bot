import os
import sys
import requests


WEBHOOKS = [
    {
        "name": "山﨑天",
        "env_name": "WEBHOOK_TEN",
    },
    {
        "name": "谷口愛季",
        "env_name": "WEBHOOK_AIRI",
    },
    {
        "name": "井上梨名",
        "env_name": "WEBHOOK_RINA_I",
    },
    {
        "name": "遠藤光莉",
        "env_name": "WEBHOOK_HIKARI",
    },
    {
        "name": "大園玲",
        "env_name": "WEBHOOK_REI",
    },
    {
        "name": "大沼晶保",
        "env_name": "WEBHOOK_AKIHO",
    },
    {
        "name": "関有美子",
        "env_name": "WEBHOOK_YUMIKO",
    },
    {
        "name": "武元唯衣",
        "env_name": "WEBHOOK_YUI",
    },
    {
        "name": "田村保乃",
        "env_name": "WEBHOOK_HONO",
    },
    {
        "name": "藤吉夏鈴",
        "env_name": "WEBHOOK_KARIN",
    },
    {
        "name": "松田里奈",
        "env_name": "WEBHOOK_RINA_M",
    },
    {
        "name": "守屋麗奈",
        "env_name": "WEBHOOK_RENA",
    },
    {
        "name": "石森璃花",
        "env_name": "WEBHOOK_RIKA",
    },
    {
        "name": "遠藤理子",
        "env_name": "WEBHOOK_RIKO",
    },
    {
        "name": "小田倉麗奈",
        "env_name": "WEBHOOK_REINA_O",
    },
    {
        "name": "中嶋優月",
        "env_name": "WEBHOOK_YUZUKI",
    },
    {
        "name": "村井優",
        "env_name": "WEBHOOK_YU",
    },
    {
        "name": "村山美羽",
        "env_name": "WEBHOOK_MIU",
    },
    {
        "name": "小池美波",
        "env_name": "WEBHOOK_MINAMI",
    },
    {
        "name": "菅井友香",
        "env_name": "WEBHOOK_YUUKA",
    },
]


def send_test_message(webhook_url, member_name):
    payload = {
        "username": "櫻坂46 Instagram Monitor",
        "content": f"テスト通知です。{member_name}用Webhookは正常に動作しています。",
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=15,
        )
    except requests.RequestException as error:
        print(f"❌ {member_name}: 通信エラー")
        print(f"   {error}")
        return False

    if response.status_code == 204:
        print(f"✅ {member_name}: Discord通知に成功しました")
        return True

    print(f"❌ {member_name}: Discord通知に失敗しました")
    print(f"   HTTPステータス: {response.status_code}")
    print(f"   Discordの返答: {response.text[:500]}")
    return False


def main():
    print("=== Discordテスト開始 ===")

    success_count = 0
    failure_count = 0
    missing_count = 0

    for webhook in WEBHOOKS:
        member_name = webhook["name"]
        env_name = webhook["env_name"]
        webhook_url = os.environ.get(env_name, "").strip()

        if not webhook_url:
            print(f"⚠️ {member_name}: {env_name} が設定されていません")
            missing_count += 1
            continue

        print(f"🔍 {member_name} のWebhookを確認中...")
        success = send_test_message(webhook_url, member_name)

        if success:
            success_count += 1
        else:
            failure_count += 1

    print()
    print("=== Discordテスト終了 ===")
    print(f"成功: {success_count}")
    print(f"失敗: {failure_count}")
    print(f"未設定: {missing_count}")

    if failure_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
