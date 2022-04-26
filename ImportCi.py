"""
导入全宋词
数据来源：https://github.com/chinese-poetry/chinese-poetry/tree/master/ci
此目录置于当前路径之下
"""
import logging
import json
import os
import re

from Model import Ci, CiPai, CiPu


def handle_data(data: dict) -> dict:
    text = "".join(data["paragraphs"])
    if "□" in text:
        return {}
    # 确定词牌
    for name in data["rhythmic"].split("・"):
        ci_pai = CiPai.get_or_none(CiPai.name == name)
        if ci_pai:
            break
    else:
        ci_pai = None
    # 匹配词谱
    # TODO 匹配词谱时进行平仄的校验
    ci_pu_id = -1
    if ci_pai:
        for ci_pu in CiPu.select().where(CiPu.ci_pai_id == ci_pai.id):
            ci_pu_para = list(filter(lambda s: len(s) > 0, re.split(r"[，。、|]", ci_pu.content)))
            text_para = list(filter(lambda s: len(s) > 0, re.split(r"[，。、]", text)))
            if len(ci_pu_para) != len(text_para):
                break
            for i in range(len(ci_pu_para)):
                if len(ci_pu_para[i]) != len(text_para[i]):
                    if ci_pai.id == 376:
                        print(ci_pu_para[i], text_para[i])
                    break
            else:
                ci_pu_id = ci_pu.id
                break
    return {
        "ci_pai_id": ci_pai.id if ci_pai else -1,
        "ci_pai_name": ci_pai.name if ci_pai else data["rhythmic"],
        "ci_pu_id": ci_pu_id,
        "author": data["author"],
        "content": text
    }


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
            Ci.insert_many(filter(lambda d: len(d) > 0, map(lambda data: handle_data(data), all_data))).execute()
