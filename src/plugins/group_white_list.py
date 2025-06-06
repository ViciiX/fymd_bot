from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot import require, get_bot
from nonebot import on_notice
from ..utils.file import DataFile

d = on_notice()

@d.handle()
async def _(bot: Bot, event: Event):
	try:
		if (event.sub_type == "invite"):
			data = DataFile("[data]")
			group_white_list = data.get("white_list.json", "groups", [])
			if (event.group_id not in group_white_list):
				print(f"GROUP QUITTED: {event.group_id}")
				await bot.send_group_msg(group_id = event.group_id, message = "未在群聊白名单内=.=")
				await bot.set_group_leave(group_id = event.group_id)
	except Exception:
		pass