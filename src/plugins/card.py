import random, os, datetime

from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot import on_fullmatch, on_message, on_regex
from nonebot.params import RegexGroup

from ..utils.file import DataFile, Item
from ..utils import util as Util
from ..utils import plugin_util as Putil

detect_pool_avaliable = on_message(block = False)
forhelp = on_regex("^卡牌帮助 (\\d+)$|^卡牌帮助$")
my_card = on_fullmatch("我的卡牌")
my_level_card = on_regex("^我的卡牌 (C|B|A|S|SSS|SSR)$")
card_pools = on_regex("^卡池 (\\d+)$|^卡池$")
get_cards = on_regex("^抽卡 (\\d+) (\\d+)$")
check = on_regex("^查看卡牌 (\\d+)$")

LINE = "——————————"
LEVELS = ['SSR', 'SSS', 'S', 'A', 'B', 'C']

@detect_pool_avaliable.handle()
async def _():
	data = DataFile("[data]/DATA/card")
	all_card = data.get_raw("cards.json")
	for pool_name, values in all_card.items():
		dtime = datetime.datetime.now()
		deadline = values.get("deadline", None)
		if (deadline != None):
			deadline = datetime.datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
			if (dtime >= deadline):
				pool_data = data.get("cards.json", pool_name, {})
				pool_data["avaliable"] = False
				data.set("cards.json", pool_name, pool_data)
				print(f"卡池{pool_name}超时，已禁用")

@forhelp.handle()
async def _(event: Event, args = RegexGroup()):
	if (args[0] == None):
		data = DataFile("[data]/DATA")
		help_dict = data.get("help.json", "card", {})
		mes = f"""【卡牌】功能列表
————————————
{"\n".join([f"{i}.{list(help_dict.keys())[i]}" for i in range(len(help_dict.keys()))])}
————————————
发送“卡牌帮助 [序号]”获取详细帮助
如：卡牌帮助 1
————————————"""
		await forhelp.finish(mes)
	else:
		data = DataFile("[data]/DATA")
		help_dict = data.get("help.json", "card", {})
		help_list = list(help_dict.keys())
		index = int(args[0])
		if (0 <= index and index <= len(help_list)-1):
			await Putil.reply(forhelp, event, f"""{help_list[index]}
————————————
{"\n".join(help_dict[help_list[index]])}""")
		else:
			await Putil.reply(forhelp, event, "404 Not Fucked")

@card_pools.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	all_card = DataFile("[data]/DATA/card").get_raw("cards.json")
	if (args[0] == None):
		mes = ["📎当前可用的所有卡池", LINE]
		all_card = get_avaliable_pools()
		for i in range(len(all_card)):
			mes.append(f"{i}.{list(all_card)[i]}")
		mes.extend([LINE, "卡池前数字为卡池id", "发送“卡池 [id]”查看详细信息"])
		await card_pools.finish("\n".join(mes))
	else:
		index = int(args[0])
		if (0 <= index and index < len(get_avaliable_pools())):
			await Putil.processing(bot, event)
			pool_name = list(get_avaliable_pools())[index]
			pool = all_card.get(pool_name)
			deadline = pool.get("deadline", None)
			mes = ["✨卡池信息✨", LINE, f"卡池名：{pool_name}", f"卡池id：{index}"]
			amounts = [len(pool.get(level, [])) for level in LEVELS]
			mes.extend([f"卡牌数：{sum(amounts)}张", f"价格：{pool.get("cost", "???")}🦌币/抽"])
			if (deadline != None):
				dtime = datetime.datetime.now()
				deadline = datetime.datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
				mes.append(f"💥限时时间： {Util.format_delta_time(deadline - dtime)}")
			else:
				mes.append(f"✅时间不限")
			mes.append(LINE)
			weight = pool.get("weight", {})
			weight_total = sum([weight.get(level) for level in LEVELS if (weight.get(level, None) != None)])
			msg = []
			for level in LEVELS:
				if (level in pool):
					mes.append(f"『{level}』{amounts[LEVELS.index(level)]}张 ({weight.get(level, 0)/weight_total*100}%)")
					msg.append(f"『{level}』级卡牌：\n" + "\n".join(pool.get(level)))
			mes.extend([LINE, "卡池介绍：", pool.get("text", "无")])
			msg.insert(0, "\n".join(mes))
			await Putil.sending(bot, event)
			await Putil.send_forward_msg(bot, event, {"bot": (Putil.bot_id, "FyMd卡池")}, [("bot", msg)])

		else:
			await card_pools.finish("卡池不存在！")

@my_card.handle()
async def _(event: Event):
	item = Item(f"[data]/user/{event.user_id}/card/mycard.json")
	cards = {}
	mes = [f"{event.sender.nickname} 的卡牌库：", LINE]
	total = 0
	for card in item.items:
		card_level = card.get("data", {}).get("level", None)
		cards[card_level] = cards.get(card_level, 0) + card.get("amount", 0)
		total += card.get("amount", 0)
	mes.append(f"总计：{total}张")
	for level, count in cards.items():
		mes.append(f"{level}级卡片： {count}张")
	mes.append(LINE)
	mes.append("发送“我的卡牌 【等级】”查看详细信息")
	await Putil.reply(my_card, event, "\n".join(mes))

@my_level_card.handle()
async def _(event: Event, args = RegexGroup()):
	item = Item(f"[data]/user/{event.user_id}/card/mycard.json")
	s = Item.format([x for x in item.items if (x.get("data", {}).get("level", None) == args[0])], "[call:get_id].【[data:level]】[name] * [amount]", callables = {"get_id": [get_id, {"items": item.items}]})
	mes = [f"{event.sender.nickname} 的『{args[0]}』级卡牌：", LINE] + s.split("\n")
	mes.append(LINE)
	mes.append("卡牌前数字为背包内卡牌id")
	mes.append("发送“查看卡牌 【卡牌id】”查看卡牌信息")
	await Putil.reply(my_level_card, event, "\n".join(mes))

@check.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	args = list(args)
	item = Item(f"[data]/user/{event.user_id}/card/mycard.json")
	index = int(args[0])
	if (0 <= index and index < len(item.items)):
		await Putil.processing(bot, event)
		current_item = item.items[index]
		path = os.path.join(DataFile("[data]/DATA/card/src").path, f"{current_item["name"]}.png")
		byte = None
		with open(path, "rb") as f:
			byte = Util.img_process(f.read())
		mes = [LINE] + f"""{current_item["name"]}
卡池：『{current_item.get("data", {}).get("pool", "?")}』
等级： 『{current_item.get("data", {}).get("level", "?")}』
拥有者：{event.sender.nickname}
拥有数量：{current_item.get("amount", "?")}""".split("\n")
		mes.append(LINE)
		text = current_item.get("data", {}).get("text", "")
		if (text != ""):
			mes.append(text)
		await Putil.sending(bot, event)
		await Putil.reply(check, event, MessageSegment.image(byte) + "\n".join(mes))
	else:
		await Putil.reply(check, event, "未找到该卡牌id！")

@get_cards.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	data = DataFile(f"[data]/user/{event.user_id}")
	pool = int(args[0])
	times = int(args[1])
	cdata = DataFile("[data]/DATA/card")
	if (0 <= pool and pool < len(get_avaliable_pools())):
		if (0 < times and times <= 20):
			pool_name = get_avaliable_pools()[pool]
			cost = int(cdata.get("cards.json", pool_name, {}).get("cost", "???"))
			if (data.remove_num("profile", "coin", times * cost)):
				await Putil.processing(bot, event)
				cards = get_card(pool_name, times)
				item = Item(f"[data]/user/{event.user_id}/card/mycard.json")
				mes = [f"{event.sender.nickname} 的{times}连抽卡记录", f"卡池：{pool_name}", f"卡牌图片为缩略图，原图请在“我的卡牌”中查看"]
				for card in cards:
					level = pick_level(pool_name, card)
					item.add(card, 1, {"level": level, "pool": pool_name, "text": cdata.get("cards.json", pool_name, {}).get("card_hint", "")})
					mes.append(MessageSegment.image(Util.thumbnail(os.path.join(cdata.path, f"src/{card}.png"), (100, 150))))
					mes.append({"S": "✨Nice！✨\n", "SSS": "🎉Ohhhhhh！🎉\n", "SSR": "🎊👑这、这是？！👑🎊\n"}.get(level, "") + f"恭喜你抽到了『{level}』级卡牌：\n{card}！" + {"S": "\nGood Luck！", "SSS": "\n欧皇！", "SSR": "\n哇！金色传说！！"}.get(level, ""))
				await Putil.sending(bot, event)
				await Putil.send_forward_msg(bot, event, {"bot": [Putil.bot_id, "FyMd抽卡"]}, [("bot", mes)])
			else:
				await Putil.reply(get_cards, event, f"需要{times * cost}🦌币！")
		else:
			await Putil.reply(get_cards, event, "最大只能20连哦！")
	else:
		await Putil.reply(get_cards, event, "卡池不存在！")

def get_card(pool, count):
	data = DataFile("[data]/DATA/card")
	pool =  data.get("cards.json", pool, {})
	all_card = [pool.get(x) for x in LEVELS if (pool.get(x, None) != None)]
	weight = pool.get("weight", {})
	weight = [weight.get(level) for level in LEVELS if (weight.get(level, None) != None)]
	result = []
	for i in range(count):
		choice_card = random.choices(all_card, weight)
		result.append(random.choice(choice_card[0]))
	return result

def pick_level(pool_name, name):
	all_card = DataFile("[data]/DATA/card").get("cards.json", pool_name, {})
	for level in LEVELS:
		if (name in all_card.get(level, [])):
			return level
	return None

def get_id(item, items):
	return items.index(item)

def get_by_id(_id):
	ac = get_all_card()
	try:
		return ac[_id]
	except Exception as e:
		return -1

def get_all_card():
	all_card = DataFile("[data]/DATA/card").get_raw("cards.json")
	ac = []
	for pool, value in all_card.items():
		for level in LEVELS:
			ac.extend(value.get(level, []))
	return ac

def get_avaliable_pools():
	all_card = DataFile("[data]/DATA/card").get_raw("cards.json")
	result = []
	for pool_name, values in all_card.items():
		if (values.get("avaliable", True) == True):
			result.append(pool_name)
	return result