import os
from datetime import datetime, timezone
from urllib.parse import urljoin
from xml.sax.saxutils import escape

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


ARTICLE_URL = (
    "https://sakurazaka46.com/s/s46/diary/detail/"
    "70909?ima=0000&cd=blog"
)

BASE_URL = "https://sakurazaka46.com"
FEED_URL = "https://kiki-o0.github.io/sakurazaka46blog-bot/kojima-nagisa.xml"


def main():
    response = requests.get(
        ARTICLE_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    article_body = soup.find(class_="box-article")

    if article_body is None:
        raise RuntimeError("本文エリアが見つかりません")

    main_p = article_body.find("p")

    if main_p is None:
        raise RuntimeError("本文のp要素が見つかりません")

    for tag in main_p.find_all(["script", "style", "noscript"]):
        tag.decompose()

    image_html = []

    for image in main_p.find_all("img"):
        source = (
            image.get("src")
            or image.get("data-src")
            or image.get("data-original")
            or image.get("data-lazy-src")
            or ""
        )

        if not source:
            continue

        image_url = urljoin(BASE_URL, source)
        safe_url = escape(image_url, quote=True)

        image_html.append(
            '<p><a href="' + safe_url + '">'
            '<img src="' + safe_url + '" '
            'alt="小島凪紗 公式ブログ画像">'
            "</a></p>"
        )

        image.decompose()

    text_parts = []

    for child in main_p.contents:
        if isinstance(child, NavigableString):
            text = " ".join(str(child).split())

            if text:
                text_parts.append("<p>" + escape(text) + "</p>")

        elif isinstance(child, Tag):
            if child.name == "br":
                continue

            text = " ".join(child.get_text(" ", strip=True).split())

            if text:
                text_parts.append("<p>" + escape(text) + "</p>")

    text_html = "
".join(text_parts)
    images_html = "
".join(image_html)
    content_html = text_html + "
" + images_html

    title_tag = soup.find("title")
    title = (
        title_tag.get_text(" ", strip=True)
        if title_tag is not None
        else "小島凪紗 公式ブログ"
    )

    updated = datetime.now(timezone.utc).isoformat()

    feed_xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>櫻坂46｜小島凪紗 公式ブログ</title>
  <id>{feed_id}</id>
  <updated>{updated}</updated>
  <link href="{feed_id}" rel="self"/>
  <entry>
    <title>{title}</title>
    <id>{article_id}</id>
    <link href="{article_id}"/>
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
        feed_id=escape(FEED_URL),
        updated=escape(updated),
        title=escape(title),
        article_id=escape(ARTICLE_URL),
        content=content_html,
    )

    os.makedirs("feeds", exist_ok=True)

    with open("feeds/kojima-nagisa.xml", "w", encoding="utf-8") as file:
        file.write(feed_xml)

    print("Atomフィードを生成しました")
    print("画像を本文の後ろへ配置しました")
    print("画像枚数:", len(image_html))
    print("ファイル: feeds/kojima-nagisa.xml")


if __name__ == "__main__":
    main()
