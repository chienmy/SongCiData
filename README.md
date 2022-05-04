# 宋词数据库构建

![](https://img.shields.io/badge/python-%3E%3D3.8-blue) ![](https://img.shields.io/tokei/lines/github/chienmy/SongCiData)

## 数据来源

- [诗词吾爱网](http://52shici.com/index.php)
- [中华古诗词数据库 chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)

## 运行准备

- 安装依赖：`pip install beautifulsoup4 lxml peewee requests`，如需要运行`ApiServer.py`还需安装`flask`。
- 准备数据：下载[中华古诗词数据库](https://github.com/chinese-poetry/chinese-poetry)，并将`ci`文件夹复制到当前目录。

## 脚本说明

按下列顺序运行脚本，生成`Sqlite`数据库文件。

- `ImportCiPaiAndCiPu.py`: 爬取词牌和词谱
- `ImportYunBiao.py`: 爬取汉字声韵
- `ImportCi.py`: 读取全宋词
- `ImportCiZu.py`: 文本分词

注：`ApiServer.py`文件作为[SongCiApp](https://github.com/chienmy/SongCiApp)的后端服务。
