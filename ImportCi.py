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


def handle_data(data: dict) -> dict:
    """
    处理宋词json文件中每一项
    :param data: 单个数据
    :return: 存入数据库的字典
    """
    text = "".join(data["paragraphs"])
    # 去除原文中的书名号
    text = re.sub(r"[《》]", "", text)
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
    return {
        "ci_pai_id": ci_pai.id if ci_pai else -1,
        "ci_pai_name": ci_pai.name if ci_pai else data["rhythmic"],
        "ci_pu_id": ci_pu_id_list[0][0] if len(ci_pu_id_list) > 0 else -1,
        "author": data["author"],
        "content": text
    }


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
                insert_data = handle_data(data)
                if len(insert_data) > 0:
                    insert_list.append(insert_data)
            Ci.insert_many(insert_list).execute()
