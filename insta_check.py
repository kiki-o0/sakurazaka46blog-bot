import html
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime


import requests


HISTORY_FILE = "insta_history.json"
WAIT_SECONDS = 5
DISCORD_WAIT_SECONDS = 1
ATOM_NS = "http://www.w3.org/2005/Atom"

RSS_URL = (
    "https://rss-bridge.org/bridge01/"
    "?action=display"
    "&bridge=InstagramBridge"
    "&context=Username"
    "&u={username}"
    "&media_type=all"
    "&format=Atom"
)


MEMBERS = [
    ("yamasaki.ten", "WEBHOOK_TEN"),
    ("airi.taniguchi.official", "WEBHOOK_AIRI"),
    ("rina_ino_", "WEBHOOK_RINA_I"),
    ("endohikari_official", "WEBHOOK_HIKARI"),
    ("ozonoreis2", "WEBHOOK_REI"),
    ("akiho_onuma_official", "WEBHOOK_AKIHO"),
    ("seki_yumiko_official", "WEBHOOK_YUMIKO"),
    ("takemotoyui_official", "WEBHOOK_YUI"),
    ("tamura.hono.official", "WEBHOOK_HONO"),
    ("fujiyoshi.karin", "WEBHOOK_KARIN"),
    ("matsudarina_official", "WEBHOOK_RINA_M"),
    ("rena_moriya_official", "WEBHOOK_RENA"),
    ("rika.ishimori.official", "WEBHOOK_RIKA"),
    ("riko.endo_official", "WEBHOOK_RIKO"),
    ("reinaodakura_official", "WEBHOOK_REINA_O"),
    ("yuzuki_nakashima_official", "WEBHOOK_YUZUKI"),
    ("yu.murai_official", "WEBHOOK_YU"),
    ("miumurayama_official", "WEBHOOK_MIU"),
    ("miichan_official", "WEBHOOK_MINAMI"),
    ("yuuka_sugai_official", "WEBHOOK_YUUKA"),
]


def make_empty_history():
    result = {}

    for username, webhook_name in MEMBERS:
        result[username] = []

    return result


def load_history():
    empty = make_empty_history()

    if not os.path.exists(HISTORY_FILE):
        print("履歴ファイルなし")
        return empty, True

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            old_data = json.load(file)
    except Exception as error:
        print("履歴読み込みエラー:", error)
        return empty, True

    history = {}
    migration = False

    for username, webhook_name in MEMBERS:
        value = old_data.get(username, [])

        if isinstance(value, list):
            history[username] = []

            for item in value:
                if item:
                    history[username].append(str(item))
        else:
            history[username] = []
            migration = True

    if set(old_data.keys()) != set(history.keys()):
        migration = True

    return history, migration


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("履歴を保存しました")


def text_from_entry(entry, name):
    tag = "{" + ATOM_NS + "}" + name
    node = entry.find(tag)

    if node is None:
        return ""

    return "".join(node.itertext()).strip()


def entry_url(entry):
    link_tag = "{" + ATOM_NS + "}link"

    for node in entry.findall(link_tag):
        href = node.attrib.get("href", "")
        rel = node.attrib.get("rel", "")

        if href and rel == "alternate":
            return href

    for node in entry.findall(link_tag):
        href = node.attrib.get("href", "")

        if href:
            return href

    return ""


def entry_images(entry):
    images = []
    link_tag = "{" + ATOM_NS + "}link"

    for node in entry.findall(link_tag):
        href = node.attrib.get("href", "")
        rel = node.attrib.get("rel", "")
        link_type = node.attrib.get("type", "")

        if rel == "enclosure":
            if href and link_type.startswith("image/"):
                if href not in images:
                    images.append(href)

    return images


def clean_text(value):
    if not value:
        return ""

    value = html.unescape(value)
    value = re.sub(r"<[^>]*>", " ", value)
    value = re.sub(r"s+", " ", value)

    return value.strip()


def format_date(value):
    if not value:
        return ""

    try:
        converted = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        return converted.astimezone().strftime(
            "%Y年%m月%d日 %H:%M"
        )
    except Exception:
        return value


def read_feed(username):
    url = RSS_URL.format(username=username)

    print("RSS取得:", username)

    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=40,
        )
    except requests.RequestException as error:
        print("RSS接続エラー:", error)
        return None

    print("RSS HTTPステータス:", response.status_code)

    if response.status_code != 200:
        print(response.text[:300])
        return None

    try:
        return ET.fromstring(response.content)
    except ET.ParseError as error:
        print("XML解析エラー:", error)
        return None


def get_posts(root):
    entry_tag = "{" + ATOM_NS + "}entry"
    entries =
