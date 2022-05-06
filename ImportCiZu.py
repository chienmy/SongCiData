import logging
import re

import jieba

from Model import Ci, CiZu, Zi, Yun


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
    Zi.drop_table(safe=False) if Zi.table_exists() else None
    Zi.create_table()
    ci_zu_data = {}
    ci_zu_next_data = {}
    zi_data = {}
    for ci in Ci.select():
        for p in re.split(r"[，。、]", ci.content):
            # 忽略包含缺字的词
            if "□" in p:
                continue
            if len(p) > 1:
                # 分词处理词组
                word_list = cut_sentence(p)
                for index, word in enumerate(word_list):
                    if len(word) <= 1:
                        continue
                    # 更新词组计数
                    if word in ci_zu_data.keys():
                        ci_zu_data[word].count += 1
                    else:
                        ci_zu = CiZu(size=len(word),
                                     c1=word[0],
                                     c2=word[1],
                                     c3=word[2] if len(word) > 2 else "",
                                     c4=word[3] if len(word) > 3 else "")
                        ci_zu_data[word] = ci_zu
                    # 更新词组下一字计数
                    if index == len(word_list) - 1:
                        continue
                    word_index = p.find(word)
                    if p[word_index + len(word)] == word_list[index + 1][0]:
                        word_next = word_list[index + 1]
                    else:
                        word_next = p[word_index + len(word)]
                    if word not in ci_zu_next_data.keys():
                        ci_zu_next_data[word] = {}
                    if word_next not in ci_zu_next_data[word].keys():
                        ci_zu_next_data[word][word_next] = 0
                    ci_zu_next_data[word][word_next] += 1
                # 处理单字，建立倒排索引
                for c in p:
                    if c not in zi_data.keys():
                        zi_data[c] = []
                    zi_data[c].append(ci.id)
    # 保存下一词组计数
    for word, word_next_dict in ci_zu_next_data.items():
        word_next_list = [(k, v) for k, v in word_next_dict.items()]
        word_next_list.sort(key=lambda x: x[1], reverse=True)
        word_next_str = []
        for k, v in word_next_list:
            # 只出现一次的不会保存
            if v == 1:
                break
            word_next_str.append("{0}|{1}".format(k, v))
        ci_zu_data[word].next_zi = "|".join(word_next_str)
    CiZu.bulk_create([ci_zu for ci_zu in ci_zu_data.values() if ci_zu.count > 1], batch_size=1000)
    # 压缩保存倒排索引
    zi_list = []
    for zi, index_list in zi_data.items():
        if Yun.select().where(Yun.value == zi).count() == 0:
            continue
        index_list.sort()
        zi_list.append(Zi(
            value=zi,
            index_list="|".join([str(index_list[0])] + [str(index_list[i + 1] - index_list[i])
                                                        for i in range(len(index_list) - 1)])
        ))
    Zi.bulk_create(zi_list, batch_size=1000)
