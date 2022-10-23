from .code.hire import *
from .code.database import init,UserInfo
import nonebot
from nonebot import get_bot
from hoshino import Service,priv
nonebot.on_startup(init)

sv_help = '''
测试
'''.strip()

sv = Service(
    name = '300英雄出租',  #功能名
    use_priv = priv.NORMAL, #使用权限   
    manage_priv = priv.ADMIN, #管理权限
    visible = True, #是否可见
    enable_on_default = True, #是否默认启用
    bundle = '娱乐', #属于哪一类
    help_ = sv_help #帮助文本
    )
    
@sv.on_fullmatch(["出租帮助"])
async def bangzhu(bot, ev):
    await bot.finish(ev, sv_help)

@sv.on_prefix(('绑定角色'))
async def bangqu(bot, ev):
    uid:int = ev.user_id
    gid:int = ev.group_id
    if name := str(ev.message):
        msg = await bangding(uid,gid,name)
        await bot.finish(ev,msg,at_sender=True)
    else:
        await bot.finish(ev,"请输入角色名",at_sender=True)

@sv.on_prefix(('绑定盒子'))
async def banghe(bot, ev):
    uid:int = ev.user_id
    if name := str(ev.message):
        if await UserInfo.set_info(uid,**{'default':name}):
            await bot.finish(ev,f"\n盒子：{name}\n绑定成功",at_sender=True)
        else:
            await bot.finish(ev,"请先进行绑定角色",at_sender=True)
    else:
        await bot.finish(ev,"请输入角色名",at_sender=True)

@sv.on_prefix(('查看角色'))
async def cbang(bot, ev):
    if ev.message[0].type == 'at':
        uid:int = ev.message[0].data['qq']
    else:
        uid:int = ev.user_id
    if user := await UserInfo.get_info(uid):
        await bot.finish(ev,f'\n角色为：{user.name}\n盒子名：{user.default}',at_sender=True)
    else:
        await bot.finish(ev,"未查询到角色绑定信息",at_sender=True)

@sv.on_prefix(('删除角色'))
async def dbang(bot, ev):
    if ev.message[0].type == 'at':
        if not priv.check_priv(ev, priv.SUPERUSER):
            await bot.finish(ev, '删除他人绑定请联系维护', at_sender=True)
            return
        uid:int = ev.message[0].data['qq']
    else:
        uid:int = ev.user_id
    if await UserInfo.del_info(uid):
        await bot.finish(ev,"解绑角色成功",at_sender=True)
    else:
        await bot.finish(ev,"未绑定角色无法删除",at_sender=True)

@sv.on_prefix(('查看状态'))
async def ckz(bot, ev):
    if ev.message[0].type == 'at':
        uid:int = ev.message[0].data['qq']
    else:
        uid:int = ev.user_id
    if user := await view_info(uid):
        print(user)
        await bot.finish(ev,f'\n角色：{user[2]}\n盒子：{user[3]}\n状态：{user[4]}\n时间：{user[8]}\n推送：{user[5]}\n胜场：{user[6]}\n收益：{user[7]}',at_sender=True)
    else:
        await bot.finish(ev,"未绑定角色无法查看",at_sender=True)

@sv.on_rex('(开启|关闭)自动推送')
async def change_arena_sub(bot, ev):
    if ev.message[-1].type == 'at':
        if not priv.check_priv(ev, priv.ADMIN):
            await bot.finish(ev, '更改他人推送仅限管理员操作', at_sender=True)
            return
        uid:int = ev.message[-1].data['qq']
    else:
        uid:int = ev.user_id
    auto = 1 if (auto := ev['match'].group(1) == '开启') else 0
    if user_info := await UserInfo.get_info(uid):
        if user_info.auto == auto:
            await bot.finish(ev,f'目前已经是{ev["match"].group(1)}状态了',at_sender=True)
        elif await UserInfo.set_info(uid,**{'auto':auto}):
            await bot.finish(ev, f'{ev["match"].group(1)}成功', at_sender=True)
        else:
            await bot.finish(ev,"请先进行绑定角色",at_sender=True)
    else:
        await bot.finish(ev,"未查询到角色绑定信息",at_sender=True)

@sv.on_prefix(('出租'))
async def cha(bot, ev):
    name =str(ev.message)
    if stats := await get_stats(name):
        msg =hire_to_chs(int(stats[0]))
        await bot.finish(ev,f'\n角色：{name}\n状态：{msg}\n时间：{stats[1]}',at_sender=True)
    else:
        await bot.finish(ev,"未查询到角色",at_sender=True)

@sv.on_prefix(('胜场'))
async def chas(bot,ev):
    name =str(ev.message)
    if roleID := await get_roleid(name):
        win_list = await get_win(roleID,2)
        await bot.finish(ev,f'\n角色：{name}\n胜场：{win_list[0]}\n收益：{win_list[1]}',at_sender=True)
    else:
        await bot.finish(ev,"未查询到角色",at_sender=True)

@sv.scheduled_job('interval', minutes=5)
async def chuzu_schedule():
    bot=get_bot()
    if user_list :=await UserInfo.get_all():
        for user in user_list:
            if user[5] == 0:
                break
            if not (RoleID :=await get_roleid(user[2])):
                await UserInfo.del_info(user[0])
                await bot.send_group_msg(
                    group_id = user[1],
                    message = f'[CQ:at,qq={user[0]}]\n角色：{user[2]}\n由于官网无法查询到角色，自动删除绑定信息')
                break
            sv.logger.info(f'querying {user[0]} for {user[3]}')
            if now_stats := await get_stats(user[3]):
                if user[4] != int(now_stats[0]):
                    if win_list := await get_win(RoleID,2):
                        if await UserInfo.set_info(user[0],**{'stats':int(now_stats[0]),'win':win_list[0]}):
                            await bot.send_group_msg(
                                group_id = user[1],
                                message = f'[CQ:at,qq={user[0]}]\n角色：{user[3]}\n状态：{hire_to_chs(int(now_stats[0]))}\n时间：{now_stats[1]}\n胜场：{win_list[0]}\n收益：{win_list[1]}')
