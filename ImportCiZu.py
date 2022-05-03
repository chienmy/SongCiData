import logging
import re

import jieba

from Model import Ci, CiZu


def cut_sentence(text):
    cut_result = jieba.lcut(text)
    if len(text) == 2:
        return [text]
    elif len(text) == 3:
        # 恰好分为12或者21，直接作为结果
        if len(text) == 2:
            return cut_result
        # 否则列出前两字和后两字
        else:
            return [text[0:2], text[1:3]]
    elif len(text) == 4:
        if text[0] in cut_result and text[3] in cut_result:
            return [text[0], text[1:3], text[3]]
        else:
            return [text[0:2], text[2:4]]
    elif len(text) == 5:
        if text[2] in cut_result:
            return [text[0:2], text[2], text[3:5]]
        else:
            if text[0:2] in cut_result:
                return [text[0:2], text[2:4], text[4]]
            elif text[3:5] in cut_result:
                return [text[0], text[1:3], text[3:5]]
            else:
                return cut_result
    elif len(text) == 6:
        return [text[0:2], text[2:4], text[4:6]]
    elif len(text) == 7:
        return [text[0:2], text[2:4]] + cut_sentence(text[4:])
    elif len(text) == 8:
        if text[0] in cut_result:
            return [text[0]] + cut_sentence(text[1:])
        elif text[0:2] in cut_result:
            return [text[0:2]] + cut_sentence(text[2:])
        else:
            return cut_result
    else:
        logging.warning(text)
        return []


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)-9s %(filename)-15s[:%(lineno)d]\t%(message)s")
    CiZu.drop_table(safe=False) if CiZu.table_exists() else None
    CiZu.create_table()
    ci_zu_data = {}
    for ci in Ci.select():
        for p in re.split(r"[，。、]", ci.content):
            # 忽略包含缺字的词
            if "□" in p:
                continue
            if len(p) > 1:
                for word in cut_sentence(p):
                    if len(word) <= 1:
                        continue
                    if word in ci_zu_data.keys():
                        ci_zu_data[word].count += 1
                    else:
                        ci_zu = CiZu(size=len(word),
                                     c1=word[0],
                                     c2=word[1],
                                     c3=word[2] if len(word) > 2 else "",
                                     c4=word[3] if len(word) > 3 else "")
                        ci_zu_data[word] = ci_zu
    CiZu.bulk_create([ci_zu for ci_zu in ci_zu_data.values() if ci_zu.count > 1], batch_size=1000)
