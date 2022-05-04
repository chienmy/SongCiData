import json
import os
from flask import Flask, request
from flask_cors import *
from playhouse.shortcuts import model_to_dict
from Model import CiPai, CiPu, Yun, CiZu

app = Flask(__name__)
app.secret_key = os.urandom(16)
CORS(app, supports_credentials=True, resources=r'/*')
CORS(app)


@app.route("/cipai", methods=["GET"])
def get_ci_pai_list():
    """ 获取所有词牌的列表 """
    return json.dumps([model_to_dict(ci_pai) for ci_pai in CiPai.select()], ensure_ascii=False)


@app.route("/cipu", methods=["GET"])
def get_ci_pu_list():
    """ 获取指定词牌的所有词谱 """
    ci_pai_id = request.args.get("cipai", 1, int)
    return json.dumps([model_to_dict(ci_pu) for ci_pu in CiPu.select().where(CiPu.ci_pai_id == ci_pai_id)],
                      ensure_ascii=False)


@app.route("/word", methods=["GET"])
def get_word_list():
    """ 获取候选词组列表 """
    # 当前输入字
    zi = request.args.get("zi", None)
    # 下一个字的韵书和谱字
    yun_book = request.args.get("book", "clzy")
    yun = request.args.get("yun", None)
    # 限制候选词的长度
    limit = request.args.get("limit", 2, int)
    if not (zi and yun):
        return "[]"
    result = []
    for ci_zu in CiZu.select().where((CiZu.c1 == zi) & (CiZu.size <= limit)).order_by(-CiZu.count):
        ping_ze_truth = _get_ping_ze_flag(ci_zu.c2, yun_book)
        # 需要检查平仄
        if not (yun == "2" or yun == "3"):
            # 确定需要平或仄
            ping_ze_target = 0 if yun == "0" or yun.islower() else 1
            if not (ping_ze_truth == 2 or (ping_ze_target == ping_ze_truth)):
                continue
        result.append({
            "id": ci_zu.id,
            "word": ci_zu.c1 + ci_zu.c2 + ci_zu.c3 + ci_zu.c4,
            "count": ci_zu.count,
            "needCheck": ping_ze_truth == -1 or ping_ze_truth == 2
        })
    return json.dumps(result, ensure_ascii=False)


@app.route("/pz/check", methods=["POST"])
def check_ping_ze():
    """ 检查平仄是否符合 -1:未知情况；0-不符合；1-符合；2-待检查 """
    req_data = json.loads(request.get_data(), encoding="utf-8")
    yun_book = req_data["book"]
    pu = req_data["pu"]
    content = req_data["content"]
    strict_flag = bool(req_data["strictMode"])
    result = []
    for i in range(len(content)):
        pu_flag = pu[i]
        # 严格模式
        if strict_flag:
            if pu_flag == "2":
                pu_flag = "0"
            if pu_flag == "3":
                pu_flag = "1"
        if content[i] == " ":
            result.append(-1)
        elif pu_flag in list("23"):
            result.append(1)
        else:
            ping_ze_truth = _get_ping_ze_flag(content[i], yun_book)
            if ping_ze_truth == -1 or ping_ze_truth == 2:
                result.append(ping_ze_truth)
            elif pu_flag == "0" or ord("a") <= ord(pu_flag) <= ord("z"):
                result.append(1 if ping_ze_truth == 0 else 0)
            elif pu_flag == "1" or ord("A") <= ord(pu_flag) <= ord("Z"):
                result.append(1 if ping_ze_truth == 1 else 0)
    return json.dumps(result, ensure_ascii=False)


@app.route("/yun/check", methods=["POST"])
def check_yun():
    """
    检查韵字是否符合
    -1: 未知情况；0 - 不符合；1 - 符合；2 - 不确定
    """
    req_data = json.loads(request.get_data(), encoding="utf-8")
    yun_book = req_data["book"]
    yun_list = req_data["yun"]
    yun_group = req_data["yunGroup"]
    all_result = []
    for i in range(len(yun_list)):
        # 本组韵的校验结果
        result = [-1 for _ in range(len(yun_group[i]))]
        # 本组韵可能的韵部
        possible_yun = []
        for c in yun_group[i]:
            if len(c) != 0:
                possible_yun.append(set([y.part for y in Yun.select().where((Yun.value == c) & (Yun.book == yun_book))]))
        # 仅有单字
        if len(possible_yun) == 1:
            # 该字一定符合
            for j, c in enumerate(yun_group[i]):
                if len(c) != 0:
                    result[j] = 1
        # 多字
        elif len(possible_yun) > 1:
            yun_set = possible_yun[0].intersection(*possible_yun[1:])
            for j, c in enumerate(yun_group[i]):
                if len(c) != 0:
                    # 交集为空，每个字都为不符合状态
                    if len(yun_set) == 0:
                        result[j] = 0
                    # 交集不为空，单韵部为符合，多韵部为不确定
                    else:
                        if Yun.select().where((Yun.value == c) & (Yun.book == yun_book)).count() == 1:
                            result[j] = 1
                        else:
                            result[j] = 2
        all_result.append(result)
    return json.dumps(all_result, ensure_ascii=False)


def _get_ping_ze_flag(c: str, yun_book: str):
    """
    :param c: 待查询字符
    :param yun_book: 韵书
    :return -1 无字；0 平；1 仄；2 皆可
    """
    ping_ze_flag = -1
    for yun in Yun.select().where((Yun.value == c) & (Yun.book == yun_book)):
        if ping_ze_flag == -1:
            ping_ze_flag = yun.ping_ze
        elif ping_ze_flag != yun.ping_ze:
            return 2
    return ping_ze_flag


if __name__ == "__main__":
    app.run(debug=True, port=8080)
