from datetime import datetime
from typing import Dict, List, Optional, Union
from hoshino import aiorequests
from nonebot import get_bot

from .config import get_config
from .database import UserInfo, add_info

true_url = get_config("hire_api", "true_url")
false_url = get_config("hire_api", "false_url")

Normal_url = get_config("hero_api", "searchNormal")
Matchs_url = get_config("hero_api", "searchMatchs")

# 绑定角色
async def bangding(uid,gid,name: str):
    name_byte = len(name.encode("gbk"))
    if name_byte > 14:
        return f"仅支持14字节以内的ID，目前字节：{name_byte}"
    if await UserInfo.get_info(uid):
        return (
            f"\n角色修改为：\n{name}"
            if await UserInfo.set_info(uid, **{"gid":gid,"name": name})
            else "绑定发生错误"
        )
    await add_info(uid,gid,name)
    return f"\n角色：{name}\n绑定成功！"

#转换出租状态
def hire_to_chs(stats):
    if stats == 1:
        return "出租中"
    elif stats == 0:
        return "待租"
    else:
        return "下架"

#获取roleid
async def get_roleid(name):
    if data := await aiohttp_post(Normal_url,{"RoleName":name}):
        return int(data["RoleID"])

#查看状态
async def view_info(uid):
    if not (user_info := await UserInfo.get_info(uid)):
        return
    if stats := await view_stats(uid):
        auto = "开启" if user_info.auto == 1 else "关闭"
        if win_list := await view_win(uid):
            return [user_info.uid, user_info.gid, user_info.name, user_info.default, hire_to_chs(int(stats[0])), auto, win_list[0], win_list[1],stats[1]]

#查看战场胜场，并保存
async def view_win(uid):
    if not (user_info := await UserInfo.get_info(uid)):
        return
    if RoleID :=await get_roleid(user_info.name):
        if win_list := await get_win(RoleID,2):
            if await UserInfo.set_info(uid,**{'win':win_list[0]}):
                return win_list

#获取出租状态
async def view_stats(uid):
    if not (user_info := await UserInfo.get_info(uid)):
        return
    if stats := await get_stats(user_info.default):
        if await UserInfo.set_info(uid,**{'stats':int(stats[0])}):
            return stats

async def aiohttp_get(url) -> Optional[List[Dict[str, Union[int, str]]]]:
    if res := await aiorequests.get(url):
        if res.status_code != 200:
            return

        if res := await res.json():
            return res["data"]

async def aiohttp_post(url,data):
    if res := await aiorequests.post(url,data):
        if res.status_code != 200:
            return

        if res := await res.json():
            return res["data"]

async def get_stats(name):
    stats_start:int = 0
    stats_close:int = 0
    hire_time=''
    if not (true_data := await aiohttp_get(true_url)):
        return
    for item in true_data:
        if item["F角色名"] == str(name):
            stats_start:int = 1
            hire_time = str(item["F订单时间"])
    if false_data := await aiohttp_get(false_url):
        for item in false_data:
            if item["F角色名"] == str(name):
                stats_close:int = 1
    else:
        return
    if stats_start != stats_close:
        return ['1',hire_time] if stats_start == 1 else ['0','无']
    else:
        return ['-1','无']


async def get_match(id:int,match:int,page:int):
    if data := await aiohttp_post(Matchs_url,{"RoleID":id,"MatchType":match,"searchIndex":page}):
        return data["Matchs"]["Matchs"]

async def get_nowwin(time:int):
    now_time=datetime.now().date().strftime('%Y-%m-%d')
    match_time= datetime.strftime(datetime.fromtimestamp(time),'%Y-%m-%d')
    return now_time == match_time

#得到胜场和收益
async def get_win(id:int,match:int):
    win = 0
    i = 0
    get_money = 0
    while (i:=i+1):
        if info := await get_match(id,match,i):
            for item in info:
                Result = int(item['Players'][0]['Result'])
                time = int(item['CreateTime'])
                if await get_nowwin(time) and Result == 1:
                    win += 1
                    money= int(item['Players'][0]['AwardMoney'])
                    get_money += money
                elif not await get_nowwin(time):
                    return [str(win),str(get_money)]
    return [str(win),str(get_money)]