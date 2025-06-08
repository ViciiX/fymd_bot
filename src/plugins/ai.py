import asyncio
from zhipuai import ZhipuAI

from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot import on_fullmatch, on_message, on_regex
from nonebot.params import RegexGroup

from ..utils.file import DataFile, Item, Logger
from ..utils import util as Util
from ..utils import plugin_util as Putil
from ..utils import image_util as ImageUtil

api_key = DataFile("[data]").get("AI.json", "api_key", None)
client = ZhipuAI(api_key = api_key)

chat = on_regex("chat ([\\s\\S]+)")
switch = on_regex("role (.+)")

@chat.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	user_data = DataFile(f"[data]/user/{event.user_id}", Logger(f"[data]/user/{event.user_id}/log/coin.log", "AI聊天"))
	if (args[0] == "new"):
		user_data.set("ai/chat.json", "history", [])
		await Putil.reply(chat, event, "已开启新对话", True)
	prompt = DataFile("[data]").get("AI.json", "prompt")
	history = user_data.get("ai/chat.json", "history", [])
	prompt = prompt.get(user_data.get("ai/chat.json", "role", "glm"))
	task_data = DataFile("[data]")
	task_amount = task_data.get("AI.json", "task", 0)
	if (task_amount < 25):
		if (user_data.remove_num("profile", "coin", 1)):
			history.append(text_message("user", args[0]))
			await Putil.processing(bot, event)
			task_data.add_num("AI.json", "task", 1)
			try:
				reply = await request([text_message("system", prompt)] + history, args[0])
			except Exception:
				await Putil.reply(chat, event, "（看来有一股禁忌的力量干扰了对话）", True)
			task_data.remove_num("AI.json", "task", 1)
			if (reply.split("</think>")[1].strip() == "[system]开启新对话"):
				user_data.set("ai/chat.json", "history", [])
				await Putil.reply(chat, event, "已开启新对话", True)
			history.extend([text_message("user", args[0]), text_message("assistant", reply)])
			while (len(history) > 1000):
				history.pop(0)
			user_data.set("ai/chat.json", "history", history)
			print(reply)
			mes = [f"[{event.sender.nickname}]\n{args[0]}", "", f"[Bot]\n{reply.split("</think>")[1].strip()}"]
			await Putil.sending(bot, event)
			await Putil.reply(chat, event, MessageSegment.image(ImageUtil.text_to_image(mes, width = [8, 2], qq = event.user_id)))
		else:
			await Putil.reply(chat, event, "需要1个鹿币")
	else:
		await Putil.reply(chat, event, "当前请求过多")

@switch.handle()
async def _(event: Event, args = RegexGroup()):
	user_data = DataFile(f"[data]/user/{event.user_id}")
	prompt = DataFile("[data]").get("AI.json", "prompt")
	if (args[0] in prompt):
		user_data.set("ai/chat.json", "role", args[0])
		await Putil.reply(switch, event, f"已将角色切换至：{args[0]}")
	else:
		await Putil.reply(switch, event, f"角色不存在！\n当前支持角色：\n{"、".join(list(prompt.keys()))}")

async def get_content(id):
	task_status = ''
	get_cnt = 0

	while task_status != 'SUCCESS' and task_status != 'FAILED' and get_cnt <= 40:
		result_response = client.chat.asyncCompletions.retrieve_completion_result(
			id=id)
		task_status = result_response.task_status
		if (task_status == "SUCCESS"):
			return result_response.choices
		await asyncio.sleep(2)
		get_cnt += 1


async def request(mes, text):
	mes.append(text_message("user", text))
	response = client.chat.asyncCompletions.create(
		model = "glm-z1-flash",
		messages = mes,
		tools = [{
			"type": "web_search",
			"web_search": {
				"search_engine": "search_pro_bing",
				"enable": True
			}
		}]
	)
	mes = await get_content(response.id)
	return mes[0].message.content

def text_message(role, text):
	return {
		"role": role,
		"content": text
	}

async def main():
	while True:
		text = input("[User]")
		print("思考中...")
		reply = await request(history, text)
		print("[Bot]"+reply+"\n")
		history.extend([text_message("user", text), text_message("assistant", reply)])