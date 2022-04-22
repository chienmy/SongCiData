import json
import logging

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString


def save_all_cipai():
    result = {}
    # 遍历词牌分类及url
    r = requests.get("https://52shici.com/zd/cipai.php")
    soup = BeautifulSoup(r.text, features="lxml")
    for div in soup.find_all(name="div", class_="box filter"):
        # 词牌分类
        category = div.find("h1").contents[0].strip()
        # 保存词牌名和对应url
        for a in div.find(name="ul").find_all(name="a"):
            result[a.string] = {
                "name": a.string,
                "category": category,
                "url": "https://52shici.com/zd/" + a["href"]
            }
    for name in result.keys():
        logging.info(name)
        result[name].update(save_one_cipai(result[name]["url"]))
    return result


def save_one_cipai(url: str) -> dict:
    r = requests.get(url)
    soup = BeautifulSoup(r.text, features="lxml")
    # 词牌描述
    description = soup.find(id="cipaiBox").contents[2].strip().replace(" ", "")
    # 各作者体例
    authors = {}
    for a in soup.find(id="ti").find_all(name="a"):
        author_name = a.string.strip()
        authors[author_name] = {
            "name": author_name,
            "url": "https://52shici.com/zd/pu.php" + a["href"],
            "main": "class" in a.attrs
        }
        logging.info("\t" + author_name)
        authors[author_name].update(save_ti(authors[author_name]["url"]))
    return {
        "description": description,
        "authors": authors
    }


def save_ti(url: str) -> dict:
    r = requests.get(url)
    soup = BeautifulSoup(r.text, features="lxml")
    # 说明
    description = "".join(map(lambda s: s.strip() if isinstance(s, NavigableString) else "",
                              soup.find(id="description").contents))
    # 简介
    introduction = soup.find(name="span", class_="intro").string.strip()
    div = soup.find(id="gl")
    # 示例
    examples = []
    for child in div.contents:
        if isinstance(child, NavigableString):
            s = child.strip()
            if s != "":
                examples.append(child.strip())
    # 词谱
    pu = []
    for p in div.find_all(class_="pu"):
        s = ""
        for child in p.contents:
            if isinstance(child, NavigableString):
                for c in child:
                    if c == "平":
                        s += "0"
                    elif c == "仄":
                        s += "1"
                    else:
                        s += c
            else:
                if child.name != "em":
                    continue
                if "m-p" in child["class"]:
                    s += "2"
                elif "m-z" in child["class"]:
                    s += "3"
                elif "yun-p" in child["class"] or "yun-z" in child["class"]:
                    n = 1
                    if len(child["class"]) > 1:
                        n = int(child["class"][1][1])
                    if "yun-p" in child["class"]:
                        s += chr(ord("a") + n - 1)
                    else:
                        s += chr(ord("A") + n - 1)
        pu.append(s.strip())
    return {
        "description": description,
        "pu": pu,
        "examples": examples,
        "introduction": introduction
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)-9s %(filename)-15s[:%(lineno)d]\t%(message)s")
    with open("cipai.json", "w") as f:
        f.write(json.dumps(save_all_cipai(), indent=4, separators=(',', ':')))
