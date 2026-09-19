import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
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

    image_url = urljoin(BASE_URL, src)

    img["src"] = image_url
    img["alt"] = img.get("alt") or "小島凪紗 公式ブログ画像"

    link = article_body.new_tag("a", href=image_url)
    img.wrap(link)

content_html = article_body.decode_contents()

title = soup.title.get_text(" ", strip=True)
updated = datetime.now().astimezone().isoformat()

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

with open("kojima-nagisa.xml", "w", encoding="utf-8") as f:
    f.write(feed_xml)

print("Atomフィードを生成しました")
print("ファイル: kojima-nagisa.xml")
