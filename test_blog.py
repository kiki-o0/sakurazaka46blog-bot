import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://sakurazaka46.com/s/s46/diary/detail/70909?ima=0000&cd=blog"

headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(url, headers=headers, timeout=15)
res.raise_for_status()

soup = BeautifulSoup(res.text, "html.parser")

print(soup.title.get_text(strip=True))

article_body = soup.find(class="box-article")

if article_body:
    for tag in article_body.find_all(["script", "style", "noscript"]):
        tag.decompose()

    for img in article_body.find_all("img"):
        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-original")
            or ""
        )

        if not src:
            img.decompose()
            continue

        image_url = urljoin("https://sakurazaka46.com", src)

        img["src"] = image_url
        img["alt"] = img.get("alt") or "小島凪紗 公式ブログ画像"

        link = article_body.new_tag("a", href=image_url)
        img.wrap(link)

    content_html = article_body.decode_contents()

    print("本文HTMLを作成できました")
    print(content_html[:1000])
else:
    print("本文エリアが見つかりません")
