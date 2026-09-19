import requests
from bs4 import BeautifulSoup, NavigableString, Tag

ARTICLE_URL = (
    "https://sakurazaka46.com/s/s46/diary/detail/"
    "70909?ima=0000&cd=blog"
)

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(ARTICLE_URL, headers=headers, timeout=15)
res.raise_for_status()

soup = BeautifulSoup(res.text, "html.parser")
article_body = soup.find(class_="box-article")

if not article_body:
    raise RuntimeError("本文エリアが見つかりません")

main_p = article_body.find("p")

if not main_p:
    raise RuntimeError("本文のp要素が見つかりません")

print("=== p直下の子要素の順番 ===")

for index, child in enumerate(main_p.contents, start=1):
    if isinstance(child, NavigableString):
        text = " ".join(str(child).split())
        if text:
            print(f"{index}: TEXT: {text[:100]}")
    elif isinstance(child, Tag):
        if child.name == "img":
            print(f"{index}: IMG: {child.get('src', '')}")
        else:
            text = " ".join(child.get_text(" ", strip=True).split())
            images = len(child.find_all("img"))
            print(
                f"{index}: TAG={child.name}, "
                f"images={images}, text={text[:100]}"
            )
