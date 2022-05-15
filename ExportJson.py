import json

from Model import CiPai, CiPu, Yun, CiZu, Zi
from playhouse.shortcuts import model_to_dict


def export_ci_pai():
    with open("ciPai.json", "w") as f:
        json_str = json.dumps([model_to_dict(ci_pai) for ci_pai in CiPai.select()], ensure_ascii=False)
        f.write(json_str)


def export_ci_pu():
    with open("ciPu.json", "w") as f:
        json_str = json.dumps([model_to_dict(ci_pu) for ci_pu in CiPu.select()], ensure_ascii=False)
        f.write(json_str)


def export_yun():
    with open("yun.json", "w") as f:
        result = []
        book_list = ["psy", "clzy", "zhxy", "zhty"]
        for yun in Yun.select():
            d = model_to_dict(yun)
            d["book"] = book_list.index(yun.book)
            result.append(d)
        f.write(json.dumps(result, ensure_ascii=False))


def export_ci_zu():
    with open("ciZu.json", "w") as f:
        result = []
        for ci_zu in CiZu.select():
            if ci_zu.count == 1:
                continue
            word = "".join([ci_zu.c1, ci_zu.c2, ci_zu.c3, ci_zu.c4])
            result.append({
                "id": ci_zu.id,
                "word": word,
                "count": ci_zu.count,
                "next_zi": ci_zu.next_zi
            })
        f.write(json.dumps(result, ensure_ascii=False))


def export_zi():
    with open("zi.json", "w") as f:
        json_str = json.dumps([model_to_dict(zi) for zi in Zi.select()], ensure_ascii=False)
        f.write(json_str)


if __name__ == "__main__":
    export_ci_pai()
    export_ci_pu()
    export_yun()
    export_ci_zu()
    export_zi()
