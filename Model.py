from peewee import Model, SqliteDatabase, AutoField, TextField, IntegerField


class BaseModel(Model):
    class Meta:
        database = SqliteDatabase("./SongCi.db")


class CiPai(BaseModel):
    """ 词牌 """
    id = AutoField()
    # 词牌名
    name = TextField(index=True)
    # 词牌介绍
    description = TextField(default="")


class CiPu(BaseModel):
    """ 词谱 """
    id = AutoField()
    # 词牌ID
    ci_pai_id = IntegerField(index=True)
    # 作者
    author = TextField()
    # 字数
    size = IntegerField()
    # 词谱，分段以|分隔
    content = TextField()
    # 示例，分段以|分隔
    example = TextField()
    # 介绍
    description = TextField()
    # 韵律简介
    introduction = TextField()
    # 是否优先展示
    main_flag = IntegerField(default=0)
    # 对偶句式，一组4个数字，逗号分隔
    dual_part = TextField(default="")
    # 叠韵句式，一组4个数字，逗号分隔
    overlap_part = TextField(default="")
    # 关键单字，数字，逗号分隔
    mark_part = TextField(default="")


class Ci(BaseModel):
    """ 全宋词 """
    id = AutoField()
    # 词牌ID，如果本数据库中存在则为词牌id，否则为-1
    ci_pai_id = IntegerField(default=-1)
    # 词牌
    ci_pai_name = TextField(default="")
    # 词谱ID
    ci_pu_id = IntegerField(default=-1)
    # 作者
    author = TextField()
    # 正文
    content = TextField()


class Yun(BaseModel):
    """ 韵表 """
    id = AutoField()
    # 所属韵书
    book = TextField()
    # 韵部
    part = TextField()
    # 平仄，0为平声，1为仄声
    ping_ze = IntegerField(default=0)
    # 字
    value = TextField()


class CiZu(BaseModel):
    """ 词组 """
    id = AutoField()
    # 词组长度
    size = IntegerField()
    # 最多支持四字词组
    c1 = TextField(default="", index=True)
    c2 = TextField(default="", index=True)
    c3 = TextField(default="", index=True)
    c4 = TextField(default="", index=True)
    # 出现次数计数
    count = IntegerField(default=1)
    # 下一字预测
    next_zi = TextField(default="")


class Zi(BaseModel):
    id = AutoField()
    value = TextField(index=True)
    index_list = TextField()
