from email.policy import default
from tortoise.models import Model
from tortoise import fields
from tortoise import Tortoise
from os.path import dirname, join


class UserInfo(Model):
    uid = fields.IntField(unique=True,index=True)
    gid = fields.IntField(index=True)
    name = fields.TextField()
    default = fields.TextField()
    stats = fields.IntField(default=-1)
    auto = fields.IntField(default=0)
    win = fields.IntField(default=0)
    class Meta:
        table = 'user'

    #获取全部用户
    @classmethod
    async def get_all(cls):
        if user_list := await cls.all().values_list('uid','gid','name','default','stats','auto','win'):
            return user_list

    #获取用户信息
    @classmethod
    async def get_info(cls, uid:int):
        if user := await cls.get_or_none(uid=uid):
            return user

    #删除用户
    @classmethod
    async def del_info(cls,uid:int):
        if info := await cls.get_or_none(uid=uid):
            await info.delete()
            return True

    #修改任意数据
    @classmethod
    async def set_info(cls,uid:int,**kwargs):
        if await cls.get_or_none(uid=uid):
            await cls.filter(uid=uid).update(**kwargs)
            return True

async def init():
    await Tortoise.init(
        db_url='sqlite:///'+join(dirname(__file__),'user_info.db'),
        modules={'models': [__name__]}
    )
    await Tortoise.generate_schemas()
#增
async def add_info(uid,gid,name):
    user_info = UserInfo(uid=uid,gid=gid,name=name,default=name)
    await user_info.save()