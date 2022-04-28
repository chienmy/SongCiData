"""
导入全宋词
数据来源：https://github.com/chinese-poetry/chinese-poetry/tree/master/ci
此目录置于当前路径之下
"""
import json
import logging
import os
import re
from typing import Tuple

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from peewee import fn

from Model import Ci, CiPai, CiPu, Yun


def handle_data(data: dict, check_text: str = "") -> Tuple[dict, str]:
    """
    处理宋词json文件中每一项
    :param data: 单个数据
    :param check_text: 直接检查原文
    :return: 存入数据库的字典
    """
    text = "".join(data["paragraphs"])
    # 去除原文中的书名号
    text = re.sub(r"[《》]", "", text)
    # 忽略包含缺字的词
    if "□" in text:
        return {}, ""
    # 确定词牌
    for name in data["rhythmic"].split("・"):
        ci_pai = CiPai.get_or_none(CiPai.name == name)
        if ci_pai:
            break
    else:
        ci_pai = None
    # 候选词谱列表
    ci_pu_id_list = []
    # 匹配词谱
    if ci_pai:
        for ci_pu in CiPu.select().where(CiPu.ci_pai_id == ci_pai.id):
            ci_pu_para = list(filter(lambda s: len(s) > 0, re.split(r"[，。、|]", ci_pu.content)))
            # 如果已给出待检查的原文，直接使用
            if len(check_text) > 0:
                text_para = check_text
            else:
                text_para = list(filter(lambda s: len(s) > 0, re.split(r"[，。、]", text)))
            # 字数不等，跳过
            if len(ci_pu_para) != len(text_para):
                continue
            # 计算平仄相似度
            match_num = 0
            for i in range(len(ci_pu_para)):
                if len(ci_pu_para[i]) != len(text_para[i]):
                    break
                for yun_c, c in zip(ci_pu_para[i], text_para[i]):
                    if match_ping_ze(c, yun_c):
                        match_num += 1
            else:
                ci_pu_id_list.append((ci_pu.id, match_num))
    # 取匹配度最高者
    ci_pu_id_list.sort(key=lambda x: x[1], reverse=True)
    # 利用诗词搜索结果获得原文
    search_result = ""
    if ci_pai and len(ci_pu_id_list) == 0:
        # 本次检查已经获取过原文
        if len(check_text) > 0:
            print(text)
            print(check_text)
        else:
            r = requests.get("https://www.52shici.com/zd/shici.php", params={
                "keyword": text[:7],
                "search": "custom",
                "filter": "content",
                "display": "宋"
            })
            soup = BeautifulSoup(r.text, features="lxml")
            div = soup.find(class_="shici-content")
            if div:
                for child in soup.find(class_="shici-content").contents:
                    if isinstance(child, NavigableString):
                        search_result += child
                    elif child.name != "br":
                        search_result += child.string
        # 搜索结果与原来一致，取消二次处理
        if search_result == text:
            search_result = ""
    return {
        "ci_pai_id": ci_pai.id if ci_pai else -1,
        "ci_pai_name": ci_pai.name if ci_pai else data["rhythmic"],
        "ci_pu_id": ci_pu_id_list[0][0] if len(ci_pu_id_list) > 0 else -1,
        "author": data["author"],
        "content": text
    }, search_result


def match_ping_ze(c: str, yun_c: str, yun_book="clzy") -> bool:
    # 查找字符的平仄
    yun_sum = Yun.select(fn.SUM(Yun.value)).where((Yun.book == yun_book) & (Yun.value == c))
    yun_list = Yun.select().where((Yun.book == yun_book) & (Yun.value == c))
    if yun_sum == 0:
        c_flag = 0
    elif yun_sum == len(yun_list):
        c_flag = 1
    else:
        c_flag = -1
    # 词谱此处的平仄
    if ord("0") <= ord(yun_c) <= ord("1"):
        yun_c_flag = int(yun_c)
    elif ord("2") <= ord(yun_c) <= ord("3"):
        yun_c_flag = -1
    elif yun_c.islower():
        yun_c_flag = 0
    else:
        yun_c_flag = 1
    # 返回判断结果
    if (c_flag < 0) or (yun_c_flag < 0):
        return True
    else:
        return c_flag == yun_c_flag


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)-9s %(filename)-15s[:%(lineno)d]\t%(message)s")
    Ci.drop_table(safe=False) if Ci.table_exists() else None
    Ci.create_table()
    for file_name in os.listdir("./ci"):
        if re.match(r"ci\.song\.\d+\.json", file_name):
            logging.info(file_name)
            with open("./ci/" + file_name, "r", encoding="utf-8") as f:
                all_data = json.load(f)
            insert_list = []
            for data in all_data:
                insert_data, check_result = handle_data(data)
                # 二次处理
                if len(check_result) > 0:
                    insert_data, check_result_2 = handle_data(data, check_text=check_result)
                    # 搜索结果可保存
                    if insert_data["ci_pai_id"] != -1 and insert_data["ci_pu_id"] != -1:
                        new_paragraphs = insert_data["content"].split("。")
                        if len(new_paragraphs) == len(data["paragraphs"]):
                            data["paragraphs"] = new_paragraphs
                        else:
                            logging.warning("paragraphs")
                            print("".join(data["paragraphs"]))
                            print(check_result)
                if len(insert_data) > 0:
                    insert_list.append(insert_data)
            Ci.insert_many(insert_list).execute()
            with open("./ci/" + file_name, "w", encoding="utf-8") as f:
                f.write(json.dumps(all_data, indent=2, ensure_ascii=False).replace(",", ", "))
