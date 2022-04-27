"""
词牌词谱数据导入脚本
数据来源：诗词吾爱网 https://52shici.com/index.php
"""
import logging
import re

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString

from Model import CiPai, CiPu


def save_all_ci_pai() -> None:
    # 遍历词牌分类及url
    r = requests.get("https://52shici.com/zd/cipai.php")
    soup = BeautifulSoup(r.text, features="lxml")
    for div in soup.find_all(id="all"):
        # 保存词牌名和对应url
        for a in div.find(name="ul").find_all(name="a"):
            try:
                logging.info(a.string)
                save_one_ci_pai(a.string, "https://52shici.com/zd/" + a["href"])
            except Exception:
                logging.error(a.string)
                continue


def save_one_ci_pai(name: str, url: str) -> None:
    r = requests.get(url)
    soup = BeautifulSoup(r.text, features="lxml")
    # 词牌描述
    description = soup.find(id="cipaiBox").contents[2].strip().replace(" ", "")
    # 保存词牌
    ci_pai_id = CiPai.insert(name=name, description=description).execute()
    for a in soup.find(id="ti").find_all(name="a"):
        logging.info("\t" + a.string.strip())
        save_ti(ci_pai_id=ci_pai_id,
                author=a.string.strip(),
                main_flag=int("class" in a.attrs),
                url="https://52shici.com/zd/pu.php" + a["href"])


def save_ti(ci_pai_id: int, author: str, main_flag: int, url: str) -> None:
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
    CiPu.insert(
        ci_pai_id=ci_pai_id,
        author=author,
        size=len(re.sub(r"[，。、|]", "", pu_str)),
        content="|".join(pu),
        example="|".join(examples),
        description=description,
        introduction=introduction,
        main_flag=main_flag,
        dual_part=",".join(map(lambda l: ",".join(map(lambda m: str(m), l)), dual_part_index)),
        overlap_part=",".join(map(lambda l: ",".join(map(lambda m: str(m), l)), overlap_part_index)),
        mark_part=",".join(map(lambda m: str(m), mark_index))
    ).execute()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)-9s %(filename)-15s[:%(lineno)d]\t%(message)s")
    # 清空并重建数据表
    CiPu.drop_table(safe=False) if CiPu.table_exists() else None
    CiPai.drop_table(safe=False) if CiPai.table_exists() else None
    CiPu.create_table()
    CiPai.create_table()
    # 开始下载数据
    save_all_ci_pai()
