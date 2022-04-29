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
    ci_pai_id = request.args.get("cipai", 1)
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
        # 需要检查平仄
        if not (yun == "2" or yun == "3"):
            # 确定需要平或仄
            ping_ze_target = 0 if yun == "0" or yun.islower() else 1
            ping_ze_truth = -1
            for yun in Yun.select().where((Yun.value == ci_zu.c2) & (Yun.book == yun_book)):
                if ping_ze_truth == -1:
                    ping_ze_truth = yun.ping_ze
                elif ping_ze_truth != yun.ping_ze:
                    ping_ze_truth = 2
                    break
            if not (ping_ze_truth == 2 or (ping_ze_target == ping_ze_truth)):
                continue
        result.append({
            "id": ci_zu.id,
            "word": ci_zu.c1 + ci_zu.c2 + ci_zu.c3 + ci_zu.c4,
            "count": ci_zu.count
        })
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    app.run(debug=True, port=8080)
