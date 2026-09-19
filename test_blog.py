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
    print(article_body.get_text("\
", strip=True)[:500])

    images = article_body.find_all("img")
    print("画像枚数:", len(images))

    for index, img in enumerate(images, start=1):
        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-original")
            or ""
        )
        print(f"画像{index}:", src)
else:
    print("本文エリアが見つかりません")
