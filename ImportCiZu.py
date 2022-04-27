import json
import logging
import re
from collections import defaultdict

import jieba

from Model import Ci, CiPu


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)-9s %(filename)-15s[:%(lineno)d]\t%(message)s")
    ci_pu = CiPu.get_or_none(CiPu.id == 1941)
    all_divide = [list() for _ in range(len(re.split(r"[，。、]", ci_pu.example)))]
    for ci in Ci.select().where(Ci.ci_pu_id == ci_pu.id):
        d_list = []
        for index, p in enumerate(re.split(r"[，。、]", ci.content)):
            d = ""
            for s in jieba.lcut(p):
                for i in range(len(s) - 1):
                    d += "0"
                d += "1"
            all_divide[index].append(d)
    for i in range(len(all_divide)):
        d = defaultdict(int)
        for s in all_divide[i]:
            d[s] += 1
        d_list = list(d.items())
        d_list.sort(key=lambda item: item[1], reverse=True)
        print(d_list[0])
        # print(list(filter(lambda s: s not in list("，。、"), jieba.lcut(ci.content))))
