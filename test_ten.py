import os
import requests

webhook_url = os.environ.get("WEBHOOK_TEST_TEN")

payload = {
    "username": "櫻坂通知ロボ（テスト）",
    "content": "🌸 test_ten へのWebhookテストです。Discord通知は正常です！"
}

response = requests.post(webhook_url, json=payload, timeout=15)
print(response.status_code)
response.raise_for_status()
