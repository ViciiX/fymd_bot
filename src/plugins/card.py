import random, os, datetime, math

from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot import on_fullmatch, on_message, on_regex
from nonebot.params import RegexGroup
from PIL import Image

from ..utils.file import DataFile, Item
from ..utils import util as Util
from ..utils import plugin_util as Putil
from ..utils import image_util as ImageUtil

detect_pool_avaliable = on_message(block = False)
my_card = on_fullmatch("我的卡牌")
my_level_card = on_regex("^我的卡牌 (C|B|A|S|SSS|SSR|c|b|a|s|sss|ssr)$")
my_all_card = on_regex("^我的全部卡牌$|^我的所有卡牌$|^查看所有卡牌$")
card_pools = on_regex("^卡池 (\\d+)$|^卡池$")
pool_progress = on_regex("^卡池进度 (\\d+)$")
get_cards = on_regex("^抽卡 (\\d+) (\\d+)$")
check = on_regex("^查看卡牌 (\\d+)$")
daily_bro = on_fullmatch("每日群友")

shop = on_fullmatch("卡牌市场")
sell = on_regex("^回收卡牌 (\\d+) (\\d+)$")
launch = on_regex("^上架 (\\d+) (\\d+)\n价格[：|:| ](\\d+)(\n介绍[：|:| ](.+))?$")

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

@card_pools.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	all_card = DataFile("[data]/DATA/card").get_raw("cards.json")
	if (args[0] == None):
		mes = ["📎当前可用的所有卡池", LINE]
		pools = get_avaliable_pools()
		for i in range(len(pools)):
			pool_name = list(pools)[i]
			pool = all_card.get(pool_name)
			status = "💥" if (pool.get("deadline", None) != None) else "✅"
			mes.append(f"{i}.{status}{pool_name}")
		mes.extend([LINE, "卡池名称前的数字为卡池id", "✅为常驻卡池, 💥为限时卡池", "发送“卡池 [id]”查看详细信息", "发送“卡池进度 [id]”查看收集进度"])
		await card_pools.finish("\n".join(mes))
	else:
		index = int(args[0])
		if (0 <= index and index < len(get_avaliable_pools())):
			await Putil.processing(bot, event)
			pool_name = get_avaliable_pools()[index]
			pool = all_card.get(pool_name)
			deadline = pool.get("deadline", None)
			mes = ["✨卡池信息✨", LINE, f"卡池名：{pool_name}", f"卡池id：{index}"]
			amounts = [len(pool.get(level, [])) for level in LEVELS]
			mes.extend([f"卡牌数：{sum(amounts)}张", f"价格：{pool.get("cost", "???")}🦌币/抽"])
			if (deadline != None):
				dtime = datetime.datetime.now()
				deadline = datetime.datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
				mes.append(f"💥限时卡池： 还剩{Util.format_delta_time(deadline - dtime)}")
			else:
				mes.append(f"✅常驻卡池")
			mes.append(LINE)
			weight = pool.get("weight", {})
			weight_total = sum([weight.get(level) for level in LEVELS if (weight.get(level, None) != None)])
			msg = []
			for level in LEVELS:
				if (level in pool):
					mes.append(f"『{level}』{amounts[LEVELS.index(level)]}张 ({round(weight.get(level, 0)/weight_total*100, 2)}%)")
					msg.append(f"『{level}』级卡牌一览：\n" + "\n".join(pool.get(level)))
			mes.extend([LINE, "卡池介绍：", pool.get("text", "无")])
			msg.insert(0, "\n".join(mes))
			await Putil.sending(bot, event)
			try:
				await Putil.send_forward_msg(bot, event, {"bot": (Putil.bot_id, "FyMd卡池")}, [("bot", msg)])
			except Exception as e:
				await card_pools.finish(MessageSegment.image(ImageUtil.text_to_image("\n\n".join(msg), width = None, qq = event.user_id)))
		else:
			await card_pools.finish("卡池不存在！")

@pool_progress.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	index = int(args[0])
	if (0 <= index and index < len(get_avaliable_pools())):
		data = DataFile("[data]/DATA/card")
		item = Item(f"[data]/user/{event.user_id}/card/mycard.json")
		pool_name = get_avaliable_pools()[index]
		pool_data = data.get("cards.json", pool_name, {})
		count = [0, 0]
		mes = [f"{event.sender.nickname} 的【{pool_name}】卡池收集进度："]
		for level in LEVELS:
			cards = pool_data.get(level, [])
			if (len(cards) != 0):
				count[1] += len(cards)
				i = 0
				for card in cards:
					if (item.find(card, None)[1] != None):
						i += 1
				count[0] += i
				mes.append(f"『{level}』级卡牌：{i}/{len(cards)} ({round(i / len(cards) * 100, 2)}%)")
		mes.append(f"总计：{count[0]}/{count[1]} ({round(count[0] / count[1] * 100, 2)}%)")
		await Putil.reply(pool_progress, event, MessageSegment.image(ImageUtil.text_to_image(mes, width = None, qq = event.user_id)))
	else:
		await Putil.reply(pool_progress, event, "卡池不存在！")

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
	mes.append("发送“我的卡牌 【等级】”查看对应等级的卡牌")
	mes.append("发送“我的全部卡牌”查看所有卡牌")
	await Putil.reply(my_card, event, "\n".join(mes))

@my_level_card.handle()
async def _(event: Event, args = RegexGroup()):
	item = Item(f"[data]/user/{event.user_id}/card/mycard.json")
	s = Item.format([x for x in item.items if (x.get("data", {}).get("level", None) == args[0].upper())], "[call:get_id].【[data:level]】[name] * [amount]", callables = {"get_id": [get_id, {"items": item.items}]})
	mes = [f"{event.sender.nickname} 的『{args[0].upper()}』级卡牌：", LINE] + s.split("\n")
	mes.append(LINE)
	mes.append("卡牌前数字为背包内卡牌id")
	mes.append("发送“查看卡牌 【卡牌id】”查看卡牌信息")
	await Putil.reply(my_level_card, event, "\n".join(mes))

@my_all_card.handle()
async def _(bot: Bot, event: Event):
	await Putil.processing(bot, event)
	item = Item(f"[data]/user/{event.user_id}/card/mycard.json")
	mes = [f"{event.sender.nickname} 的全部卡牌：\n"]
	for level in LEVELS:
		s = Item.format([x for x in item.items if (x.get("data", {}).get("level", None) == level)], "[call:get_id].【[data:level]】[name] * [amount]", callables = {"get_id": [get_id, {"items": item.items}]})
		mes.extend([LINE, f"『{level}』级卡牌：", s])
	mes.append(LINE)
	mes.append("卡牌前数字为背包内卡牌id")
	mes.append("发送“查看卡牌 【卡牌id】”查看卡牌信息")
	await Putil.sending(bot, event)
	await Putil.reply(my_all_card, event, MessageSegment.image(ImageUtil.text_to_image("\n".join(mes), qq = event.user_id)))

@check.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	args = list(args)
	item = Item(f"[data]/user/{event.user_id}/card/mycard.json")
	index = int(args[0])
	if (0 <= index and index < len(item.items)):
		await Putil.processing(bot, event)
		current_item = item.items[index]
		mes = [LINE] + f"""{current_item["name"]}
卡池：『{current_item.get("data", {}).get("pool", "?")}』
等级： 『{current_item.get("data", {}).get("level", "?")}』
拥有者：{event.sender.nickname}
拥有数量：{current_item.get("amount", "?")}
回收单价：{get_price(current_item)} 🦌币""".split("\n")
		mes.append(LINE)

		data = DataFile("[data]")
		analysis = data.get_multi_files("user", "[read]/card/mycard.json", {"items": []})
		analysis = [x["values"]["items"] for x in analysis if (x["values"] != {"items": []})]
		all_user = len(analysis)
		count = 0
		amount_count = 0
		for user_items in analysis:
			target_item = Item.value_find(user_items, current_item["name"], current_item["data"] if (current_item["data"] != {}) else None)[1]
			if (target_item != None):
				count += 1
				amount_count += target_item["amount"]
		mes.extend([f"全服拥有人数：{count}/{all_user}【{round(count / all_user * 100, 3)}%】", f"全服拥有数量：{amount_count}", f"你掌握全服【{round(current_item["amount"] / amount_count * 100, 1)}%】的【{current_item["name"]}】！", LINE])
		text = current_item.get("data", {}).get("text", "")
		if (text != ""):
			mes.append(text)
		await Putil.sending(bot, event)
		await Putil.reply(check, event, MessageSegment.image(get_card_image(current_item["name"], current_item.get("data", {}).get("level", "C"))) + "\n".join(mes))
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
			pool_data = cdata.get("cards.json", pool_name, {})
			cost = int(pool_data.get("cost", "???"))
			if (data.remove_num("profile", "coin", times * cost)):
				await Putil.processing(bot, event)
				cards = get_card(pool_name, times)
				item = Item(f"[data]/user/{event.user_id}/card/mycard.json")
				mes = [f"{event.sender.nickname} 的{times}连抽卡记录", f"卡池：{pool_name}", f"消费：{times * cost}🦌币", f"卡牌图片为缩略图，原图请发送“我的卡牌”查看"]
				level_count = {}
				for card in cards:
					card_name = card[0]
					card_data = card[1]
					level = card_data["level"]
					level_count[level] = level_count.get(level, 0) + 1
					item.add(card_name, 1, card_data, False)
					mes.append(MessageSegment.image(ImageUtil.thumbnail(get_card_image(card_name, level, False), (100, 150))))
					mes.append({"S": "✨Nice！✨\n", "SSS": "🎉Ohhhhhh！🎉\n", "SSR": "🎊👑这、这是？！👑🎊\n"}.get(level, "") + f"恭喜你抽到了『{level}』级卡牌：\n{card_name}！" + {"S": "\nGood Luck！", "SSS": "\n欧皇！", "SSR": "\n哇！金色传说！！"}.get(level, ""))
				item.save()
				total_mes = ["🎉本次抽卡获得🎉"]
				for level in LEVELS:
					if (level in level_count):
						total_mes.append(f"『{level}』级卡牌：{level_count[level]} 张！")
				mes.append("\n".join(total_mes))
				await Putil.sending(bot, event)
				try:
					await Putil.send_forward_msg(bot, event, {"bot": [Putil.bot_id, "FyMd抽卡"]}, [("bot", mes)])
				except Exception as e:
					print(f"发送带图片卡牌结果错误：{e}")
					try:
						await Putil.send_forward_msg(bot, event, {"bot": [Putil.bot_id, "FyMd抽卡"]}, [("bot", ["(图片发送失败)"]+[x for x in mes if (type(x) == str)])])
					except Exception as e:
						print(f"发送纯文字卡牌结果错误：{e}")
						await Putil.reply(get_cards, event, "消息被风控发送失败了！😭\n以下是纯文字结果：" + MessageSegment.image(ImageUtil.text_to_image("\n".join([x for x in mes if (type(x) == str)]), qq = event.user_id)))
			else:
				await Putil.reply(get_cards, event, f"需要{times * cost}🦌币！")
		else:
			await Putil.reply(get_cards, event, "最大只能20连哦！")
	else:
		await Putil.reply(get_cards, event, "卡池不存在！")

@daily_bro.handle()
async def _(bot: Bot, event: Event):
	await Putil.processing(bot, event)
	data = DataFile(f"[data]/user/{event.user_id}/card")
	time = datetime.datetime.now()
	last_time = datetime.datetime.strptime(data.get("daily.json", "last_time", (time - datetime.timedelta(days = 1)).strftime("%Y-%m-%d")), "%Y-%m-%d")
	bro = data.get("daily.json", "name", "")
	level = pick_level("_每日群友__", bro)
	if (time >= (last_time + datetime.timedelta(days = 1))):
		card = get_card("_每日群友_", 1)[0]
		item = Item(f"[data]/user/{event.user_id}/card/mycard.json")
		item.add(card[0], 1, card[1])
		bro = card[0]
		level = card[1]["level"]
		data.set("daily.json", "name", card[0])
		data.set("daily.json", "last_time", time.strftime("%Y-%m-%d"))
	mes = [LINE, f"🌸你今天的每日群友是：{bro.split(" - ")[0]}！🌸"]
	if (time >= (last_time + datetime.timedelta(days = 1))):
		mes.extend([f"✅『{level}』级卡牌：{bro}", "已收录至【我的卡牌】"])
	await Putil.sending(bot, event)
	await Putil.reply(daily_bro, event, MessageSegment.image(get_card_image(bro, add_border = False)) + "\n".join(mes))

@shop.handle()
async def _():
	data = DataFile("[data]")
	goods = data.get("shop.json", "goods", [])
	mes = ["🏬卡牌市场🏬", LINE, "✈最近上市："]
	if (len(goods) == 0):
		mes.append("无")
	for item in goods[:-6]:
		mes.append(f"{item["name"]} * {item["amount"]} - {item["cost"]}🦌币")
	mes.extend([LINE, "发送“回收卡牌 [卡牌id] [数量]”可以低价但不限量不限时地出售现有的卡牌"])
	await shop.finish("\n".join(mes))

@sell.handle()
async def _(event: Event, args = RegexGroup()):
	data = DataFile("[data]/DATA/card")
	args = [int(x) for x in args]
	user_item = Item(f"[data]/user/{event.user_id}/card/mycard.json")
	index = args[0]
	if (0 <= index and index < len(user_item.items)):
		item = user_item.items[index]
		if (item["amount"] >= args[1]):
			unit_price = get_price(item)
			price = math.floor(unit_price * args[1])
			if (price >= 1):
				item_data = Item(f"[data]/user/{event.user_id}/card/mycard.json")
				user_data = DataFile(f"[data]/user/{event.user_id}")
				print(item_data.reduce(item["name"], args[1], item["data"]))
				user_data.add_num("profile", "coin", price)
				await Putil.reply(sell, event, f"""
💰回收成功！💰
卡牌：{item["name"]}
数量：{args[1]}
单价：{round(unit_price, 2)} 🦌币/张
总额：{price} 🦌币
""".strip())
			else:
				await Putil.reply(sell, event, "金额不足1🦌币！请提高出售数量")
		else:
			await Putil.reply(sell, event, "你没有这么多卡牌！")
	else:
		await Putil.reply(sell, event, "未找到该卡牌id！")

@launch.handle()
async def _(event: Event, args = RegexGroup()):
	print(args)

def get_price(item):
	pool_data = DataFile("[data]/DATA/card").get("cards.json", item["data"]["pool"], {})
	revision = pool_data.get("sell_revision", {})
	basic_price = pool_data.get("cost", 1) * 0.1 * revision.get("scale", 1)
	weight = pool_data.get("weight")
	ratio = sum([weight.get(level, 0) for level in LEVELS]) / weight[item["data"]["level"]]
	price = basic_price * ratio
	#查找对应等级是否有自定义价格
	price = revision.get(item["data"]["level"], price)
	#查找是否有特定卡牌的自定义价格
	price = revision.get("specific", {}).get(item["name"], price)
	return price

def get_item_info(item):
	data = DataFile("[data]")
	analysis = data.get_multi_files("user", "[read]/card/mycard.json", {"items": []})
	analysis = [x["values"]["items"] for x in analysis if (x["values"] != {"items": []})]
	count = 0
	amount_count = 0
	for user_items in analysis:
		target_item = Item.value_find(user_items, item["name"], item["data"] if (item["data"] != {}) else None)[1]
		if (target_item != None):
			count += 1
			amount_count += target_item["amount"]
	return {"owner": [count, len(analysis)], "total_amount": [item["amount"], amount_count]}


def get_card(pool_name, count):
	cards = get_card_name(pool_name, count)
	cdata = DataFile("[data]/DATA/card")
	pool_data = cdata.get("cards.json", pool_name, {})
	result = []
	for card_name in cards:
		#卡牌信息（附带的文字）
		text = ""
		text_data = cdata.get("cards.json", pool_name, {}).get("card_text", {})
		text = text_data.get("general", text)
		if (text_data.get("specific", None) != None):
			for card_text, involved_cards in text_data.get("specific", None):
				if (card_name in involved_cards):
					text = card_text
		#重定向卡池
		real_pool = pool_name
		reindex_pool = pool_data.get("reindex_pool", None)
		if (reindex_pool != None):
			if (reindex_pool.get("general", None) != None):
				real_pool = reindex_pool.get("general", None)
			for re_pool, re_cards in reindex_pool.items():
				if (type(re_cards) == list and card_name in re_cards):
					real_pool = re_pool

		result.append((card_name, {"level": pick_level(pool_name, card_name), "pool": real_pool, "text": text}))
	return result

def get_card_name(pool, count):
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
	pool_data = DataFile("[data]/DATA/card").get("cards.json", pool_name, {})
	for level in LEVELS:
		if (name in pool_data.get(level, [])):
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

def get_card_image(name, level = "C", in_bytes = True, add_border = True):
	data = DataFile("[data]/DATA/card/src")
	if (add_border):
		card_img = Image.open(data.get_path(f"{name}.png")).resize((1248, 1872))
		border_img = Image.open(data.get_path(f"card_border/{level}.png"))
		mask_img = Image.open(data.get_path(f"card_border/{level}_mask.png"))
		border_img.paste(card_img, (0,0), mask_img.convert('RGBA').split()[3])
	else:
		border_img = Image.open(data.get_path(f"{name}.png")).resize((1248, 1872))
	return ImageUtil.img_to_bytesio(border_img, "PNG") if (in_bytes) else border_img