import requests
from bs4 import BeautifulSoup

url = "https://sakurazaka46.com/s/s46/diary/detail/70909?ima=0000&cd=blog"

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(url, headers=headers, timeout=15)
res.raise_for_status()

soup = BeautifulSoup(res.text, "html.parser")

print(soup.title.get_text(strip=True))

article_body = soup.find(class_="box-article")

if article_body:
    print("本文エリアを取得できました")
    print(article_body.get_text("
", strip=True)[:500])
else:
    print("本文エリアが見つかりません")
