"""
韵表数据导入脚本
数据来源：诗词吾爱网 https://52shici.com/zd/yun.js
"""
import logging
import re

import requests

from Model import Yun

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)-9s %(filename)-15s[:%(lineno)d]\t%(message)s")
    Yun.drop_table(safe=False) if Yun.table_exists() else None
    Yun.create_table()
    result = {}
    r = requests.get("https://52shici.com/zd/yun.js")
    for title, chars in re.findall(r"var (\w+)\s*=\s*[\"'](\S*)[\"'];", r.text):
        logging.info(title)
        i = title.find("_")
        # 导入数据
        for c in chars:
            Yun.insert(
                book=title[:i],
                part=title[i:].replace("_", ""),
                ping_ze=(1 if title[i + 1] in list("sqrz") else 0),
                value=c
            ).execute()
