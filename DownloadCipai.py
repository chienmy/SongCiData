import json
import logging
import re

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString


def save_all_cipai():
    result = {}
    # 遍历词牌分类及url
    r = requests.get("https://52shici.com/zd/cipai.php")
    soup = BeautifulSoup(r.text, features="lxml")
    # # 词牌分类
    # category_dict = {}
    # for div in soup.find_all(name="div", class_="box filter"):
    #     category = div.find("h1").contents[0].strip()
    #     for a in div.find(name="ul").find_all(name="a"):
    #         pass
    for div in soup.find_all(id="all"):
        # 保存词牌名和对应url
        for a in div.find(name="ul").find_all(name="a"):
            result[a.string] = {
                "name": a.string,
                "url": "https://52shici.com/zd/" + a["href"]
            }
    for name in result.keys():
        logging.info(name)
        try:
            result[name].update(save_one_cipai(result[name]["url"]))
            del result[name]["url"]
        except Exception:
            continue
    logging.info("Size: " + str(len(result)))
    return result


def save_one_cipai(url: str) -> dict:
    r = requests.get(url)
    soup = BeautifulSoup(r.text, features="lxml")
    # 词牌描述
    description = soup.find(id="cipaiBox").contents[2].strip().replace(" ", "")
    # 各作者体例
    authors = []
    for a in soup.find(id="ti").find_all(name="a"):
        author_name = a.string.strip()
        author_detail = {
            "name": author_name,
            "main": "class" in a.attrs
        }
        logging.info("\t" + author_name)
        author_detail.update(save_ti("https://52shici.com/zd/pu.php" + a["href"]))
        authors.append(author_detail)
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
    dual_part = []
    for child in div.contents:
        if isinstance(child, NavigableString):
            s = child.strip()
            if s != "":
                examples.append(child.strip())
        elif child.name == "mark":
            examples.append(child.string)
            dual_part.append(child.string)
        elif child.name == "span":
            examples.append(child.string)
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
                    elif c in ["。", "，", "、"]:
                        s += c
            else:
                if child.name == "span":
                    for c in child.string:
                        if c == "平":
                            logging.warning(child.string)
                        elif c == "仄":
                            logging.warning(child.string)
                        elif c in ["。", "，", "、"]:
                            s += c
                elif child.name != "em":
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
    # 调整例句与词谱统一
    example_str = "".join(examples)
    pu_str = "".join(pu)
    # 叠韵句
    overlap_part_index = []
    i = 0
    while (start := example_str.find("(叠)", i)) != -1:
        i = start + 3
        start = start - 3 * len(overlap_part_index)
        overlap_start = start - 1
        while overlap_start >= 0 and [overlap_start] not in ["。", "，", "、"]:
            overlap_start -= 1
        if pu_str[overlap_start + 1: start] == pu_str[2 * overlap_start - start + 1: overlap_start]:
            overlap_part_index.append([2 * overlap_start - start - 1, overlap_start, overlap_start + 1, start])
    example_str = re.sub(r"\(\S*?\)", "", example_str)
    # 重新断句
    if len(example_str) == len(pu_str):
        i = 0
        examples = []
        for pu_s in pu:
            examples.append(example_str[i:i + len(pu_s)])
            i += len(pu_s)
    else:
        logging.warning(example_str)
    # 对偶句，强调单字
    dual_part_index = []
    mark_index = []
    for s in dual_part:
        start = example_str.find(s)
        if len(s) % 2 == 1 and s[int(len(s) / 2)] == "，":
            dual_part_index.append([start, start + int(len(s) / 2), start + int(len(s) / 2) + 1, start + len(s) + 1])
        elif len(s) % 2 == 0:
            dual_part_index.append([start, start + int(len(s) / 2), start + int(len(s) / 2) + 1, start + len(s)])
        elif len(s) == 1:
            mark_index.append(start)
        else:
            logging.warning(s)
    return {
        "description": description,
        "pu": pu,
        "examples": examples,
        "introduction": introduction,
        "dual_part": dual_part_index,
        "overlap_part": overlap_part_index,
        "mark": mark_index
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)-9s %(filename)-15s[:%(lineno)d]\t%(message)s")
    with open("cipai.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(save_all_cipai(), indent=4, separators=(',', ':'), ensure_ascii=False))
