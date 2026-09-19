import os
from datetime import datetime, timezone
from urllib.parse import urljoin
from xml.sax.saxutils import escape

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


ARTICLE_URL = "https://sakurazaka46.com/s/s46/diary/detail/70909?ima=0000&cd=blog"
BASE_URL = "https://sakurazaka46.com"
FEED_URL = "https://kiki-o0.github.io/sakurazaka46blog-bot/kojima-nagisa.xml"

response = requests.get(
    ARTICLE_URL,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=15,
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")
article = soup.find(class_="box-article")

if article is None:
    raise RuntimeError("本文エリアが見つかりません")

main = article.find("p")

if main is None:
    raise RuntimeError("本文が見つかりません")

images = []

for img in main.find_all("img"):
    src = img.get("src")

    if not src:
        continue

    url = urljoin(BASE_URL, src)
    safe_url = escape(url, quote=True)

    images.append(
        '<p><a href="' + safe_url + '">'
        '<img src="' + safe_url + '" alt="公式ブログ画像">'
        "</a></p>"
    )

    img.decompose()

texts = []

for child in main.contents:
    if isinstance(child, NavigableString):
        text = " ".join(str(child).split())

        if text:
            texts.append("<p>" + escape(text) + "</p>")

    elif isinstance(child, Tag) and child.name != "br":
        text = " ".join(child.get_text(" ", strip=True).split())

        if text:
            texts.append("<p>" + escape(text) + "</p>")

content = chr(10).join(texts + images)
updated = datetime.now(timezone.utc).isoformat()

xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>櫻坂46｜小島凪紗 公式ブログ</title>
  <id>{feed_url}</id>
  <updated>{updated}</updated>
  <link href="{feed_url}" rel="self"/>
  <entry>
    <title>小島凪紗 公式ブログ</title>
    <id>{article_url}</id>
    <link href="{article_url}"/>
    <updated>{updated}</updated>
    <author>
      <name>小島凪紗</name>
    </author>
    <content type="html"><![CDATA[
{content}
    ]]></content>
  </entry>
</feed>
""".format(
    feed_url=escape(FEED_URL),
    updated=escape(updated),
    article_url=escape(ARTICLE_URL),
    content=content,
)

os.makedirs("feeds", exist_ok=True)

with open("feeds/kojima-nagisa.xml", "w", encoding="utf-8") as file:
    file.write(xml)

print("Atomフィードを生成しました")
print("画像枚数:", len(images))
