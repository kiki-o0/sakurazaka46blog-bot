import os
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urljoin
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ARTICLE_URL = (
    "https://sakurazaka46.com/s/s46/diary/detail/"
    "70909?ima=0000&cd=blog"
)

BASE_URL = "https://sakurazaka46.com"
FEED_URL = "https://example.com/feeds/kojima-nagisa.xml"

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

for tag in main_p.find_all(["script", "style", "noscript"]):
    tag.decompose()

image_tags = main_p.find_all("img")

image_html = []

for img in image_tags:
    src = (
        img.get("src")
        or img.get("data-src")
        or img.get("data-original")
        or img.get("data-lazy-src")
        or ""
    )

    if not src:
        continue

    image_url = urljoin(BASE_URL, src)

    image_html.append(
        f'<p><a href="{escape(image_url)}">'
        f'<img src="{escape(image_url)}" '
        f'alt="小島凪紗 公式ブログ画像">'
        f'</a></p>'
    )

    img.decompose()

parts = []

for child in main_p.contents:
    if isinstance(child, NavigableString):
        text = str(child).strip()

        if text:
            parts.append(f"<p>{escape(text)}</p>")

    elif isinstance(child, Tag):
        if child.name == "br":
            continue

        if child.name == "img":
            continue

        text = child.get_text(" ", strip=True)

        if text:
            parts.append(f"<p>{escape(text)}</p>")

text_html = "
".join(parts)

content_html = text_html + "
" + "
".join(image_html)

title = soup.title.get_text(" ", strip=True)
updated = datetime.now(timezone.utc).isoformat()

feed_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>櫻坂46｜小島凪紗 公式ブログ</title>
  <id>{escape(FEED_URL)}</id>
  <updated>{escape(updated)}</updated>
  <link href="{escape(FEED_URL)}" rel="self"/>

  <entry>
    <title>{escape(title)}</title>
    <id>{escape(ARTICLE_URL)}</id>
    <link href="{escape(ARTICLE_URL)}"/>
    <updated>{escape(updated)}</updated>
    <author>
      <name>小島凪紗</name>
    </author>
    <content type="html"><![CDATA[
{content_html}
    ]]></content>
  </entry>
</feed>
'''

os.makedirs("feeds", exist_ok=True)

with open("feeds/kojima-nagisa.xml", "w", encoding="utf-8") as f:
    f.write(feed_xml)

print("Atomフィードを生成しました")
print("画像を本文の後ろへ配置しました")
print("画像枚数:", len(image_html))
print("ファイル: feeds/kojima-nagisa.xml")
