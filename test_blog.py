import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ARTICLE_URL = (
    "https://sakurazaka46.com/s/s46/diary/detail/"
    "70909?ima=0000&cd=blog"
)

BASE_URL = "https://sakurazaka46.com"

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(ARTICLE_URL, headers=headers, timeout=15)
res.raise_for_status()

soup = BeautifulSoup(res.text, "html.parser")

article_body = soup.find(class_="box-article")

if not article_body:
    raise RuntimeError("本文エリアが見つかりません")

print("=== 直下要素の順番 ===")

for index, child in enumerate(
    article_body.find_all(recursive=False),
    start=1
):
    text = child.get_text(" ", strip=True)
    images = len(child.find_all("img"))

    print(
        f"{index}: "
        f"tag={child.name}, "
        f"images={images}, "
        f"text={text[:80]}"
    )
