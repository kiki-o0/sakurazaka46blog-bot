import os
import re
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

image_count = 0

# 画像をリストに分けてしまうのではなく、順序を保つためHTML内で文字列マーカーに置換します
for img in main.find_all("img"):
    src = img.get("src")

    if not src:
        img.decompose()
        continue

    url = urljoin(BASE_URL, src)
    safe_url = escape(url)

    # 後で順番通りに処理できるよう、固有の文字列に置き換える
    img.replace_with(f"__IMG_START__{safe_url}__IMG_END__")
    image_count += 1

elements = []

# main内の要素を順番に処理します
for child in main.contents:
    text_content = ""
    
    if isinstance(child, NavigableString):
        text_content = str(child)
    elif isinstance(child, Tag) and child.name != "br":
        text_content = child.get_text(" ", strip=True)
        
    if not text_content:
        continue

    # マーカーを基準に、テキストと画像を「実際のページの順序そのまま」で分割して追加します
    parts = re.split(r'__IMG_START__(.*?)__IMG_END__', text_content)
    for i, part in enumerate(parts):
        if i % 2 == 1:  # 奇数番目は画像URLのパート
            elements.append(
                '<p><a href="' + part + '">'
                '<img src="' + part + '" alt="公式ブログ画像">'
                "</a></p>"
            )
        else:  # 偶数番目は通常のテキストパート
            text = " ".join(part.split())
            if text:
                elements.append("<p>" + escape(text) + "</p>")

content = chr(10).join(elements)
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
print("画像枚数:", image_count)
