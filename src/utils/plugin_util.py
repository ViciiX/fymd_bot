from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent

from .file import DataFile

bot_id = 1415821084

async def reply(matcher, event, message, is_finish = False):
	if (isinstance(event, GroupMessageEvent)):
		if (is_finish):
			await matcher.finish(MessageSegment.reply(event.message_id)+message)
		else:
			await matcher.send(MessageSegment.reply(event.message_id)+message)
	else:
		if (is_finish):
			await matcher.finish(message)
		else:
			await matcher.send(message)

async def processing(bot, event):
	if (isinstance(event, GroupMessageEvent)):
		await bot.set_group_reaction(group_id = event.group_id, message_id = event.message_id, code = "424", is_add = True)
	else:
		await bot.send_private_msg(user_id = event.user_id, message = "处理中...")

async def sending(bot, event):
	if (isinstance(event, GroupMessageEvent)):
		await bot.set_group_reaction(group_id = event.group_id, message_id = event.message_id, code = "124", is_add = True)
	else:
		await bot.send_private_msg(user_id = event.user_id, message = "发送中...")

async def send_forward_msg(
	bot: Bot,
	event: Event,
	short_names: dict,
	raw_messages: list[tuple]):

	def to_json(short_name, content):
		info = short_names.get(short_name, [bot_id, "fymd"])
		return {
			"type": "node",
			"data": {"user_id": str(info[0]), "nickname": info[1], "content": content},
		}

	messages = []
	for mes in raw_messages:
		if (type(mes[1]) == list):
			for same_mes in mes[1]:
				messages.append(to_json(mes[0], same_mes))
		else:
			messages.append(to_json(mes[0], mes[1]))
	if (isinstance(event, GroupMessageEvent)):
		await bot.call_api("send_group_forward_msg", group_id = event.group_id, messages = messages)
	else:
		await bot.call_api("send_private_forward_msg", user_id = event.user_id, messages = messages)

async def ban(matcher, event):
	if (isinstance(event, GroupMessageEvent)):
		data = DataFile("[data]/group")
		if (data.get(event.group_id, "r18_mode", False) == False):
			await matcher.finish("⛔该功能已被禁止！！！⛔")
	else:
		users = DataFile("[data]").get("white_list.json", "users", [])
		if (event.user_id not in users):
			await matcher.finish("⛔该功能已被禁止！！！⛔")

async def get_message(bot, event, mid, count = 1):
	if (isinstance(event, GroupMessageEvent)):
		mes = await bot.get_group_msg_history(group_id = event.group_id, message_id = mid, count = count)
	else:
		mes = await bot.get_friend_msg_history(user_id = event.user_id, message_id = mid, count = count)
	return mes["messages"]

async def get_nickname(bot, qq, no_cached = True):
	name = await bot.get_stranger_info(user_id = qq, no_cached = no_cached)
	return name["nickname"]