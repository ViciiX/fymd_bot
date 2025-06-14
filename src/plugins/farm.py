from PIL import Image, ImageFont
from pilmoji import Pilmoji
import numpy as np
import math, datetime, os, random

from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot import on_fullmatch, on_message, on_regex, require
from nonebot.params import RegexGroup

from ..utils.file import DataFile, Item, Logger
from ..utils import util as Util
from ..utils import plugin_util as Putil
from ..utils import image_util as ImageUtil

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

LINE = "——————————"
src_path = DataFile("[DATA]/farm/src").path

myland = on_fullmatch("农场")
storage = on_fullmatch("仓库")
shop = on_fullmatch("农场商店")
shop_buy = on_regex("^农场购买 (\\d+) (\\d+)$")
plant = on_regex("^播种 (\\d+) (\\d+) (.+)$")
water = on_regex("^浇水 (\\d+) (\\d+)$")
uproot = on_regex("^铲除 (\\d+) (\\d+)$")
fertilize = on_regex("^施肥 (\\d+) (\\d+) (\\d+)$")
harvest = on_regex("^收获 (\\d+) (\\d+)$")
sell = on_regex("^售卖 (\\d+) (\\d+)$")

batch_plant = on_regex("^批量播种 (\\d+) (\\d+) (\\d+) (\\d+) (.+)$")
batch_water = on_regex("^批量浇水 (\\d+) (\\d+) (\\d+) (\\d+)$")
batch_uproot = on_regex("^批量铲除 (\\d+) (\\d+) (\\d+) (\\d+)$")
batch_fertilize = on_regex("^批量施肥 (\\d+) (\\d+) (\\d+) (\\d+) (\\d+)$")
batch_harvest = on_regex("^批量收获 (\\d+) (\\d+) (\\d+) (\\d+)$")
batch_sell = on_regex("^批量售卖(( \\d+[,，/]\\d+)+)$")

befree = on_fullmatch("行动修复")

@myland.handle()
async def _(bot: Bot, event: Event):
	await Putil.processing(bot, event)
	data = DataFile(f"[data]/user/{event.user_id}/farm")
	land = Farmland(data.get("farmland.json", "farmland", [{}] * 3), [data, "farmland.json", "farmland"])
	await Putil.sending(bot, event)
	await Putil.reply(myland, event, f"🌳{event.sender.nickname} 的农场🌳" + MessageSegment.image(land.get_image(datetime.datetime.now())))

@storage.handle()
async def _(bot: Bot, event: Event):
	await Putil.processing(bot, event)
	fh = Item(f"[data]/user/{event.user_id}/farm/storage.json")
	mes = [f"{event.sender.nickname} 的仓库", LINE, "- 🌾农作物"]
	crop_s = Item.format([x for x in fh.items if (x["data"].get("type", None) == "crop")], "[call:get_id].【[call:star]】[name] * [amount]", callables = {"get_id": [get_id, {"items": fh.items}], "star": [lambda x: get_star(x["data"]["star"]), {}]})
	crop_s = "空" if (crop_s == "") else crop_s
	mes.extend(crop_s.split("\n"))
	mes.extend([LINE, "- 🌱种子"])
	seed_s = Item.format([x for x in fh.items if (x["data"].get("type", None) == "seed")], "[call:get_id].[name] * [amount]", callables = {"get_id": [get_id, {"items": fh.items}]})
	seed_s = "空" if (seed_s == "") else seed_s
	mes.extend(seed_s.split("\n"))
	mes.extend([LINE, "- 📦其他"])
	other_s = Item.format([x for x in fh.items if (x["data"].get("type", None) not in ["crop", "seed"])], "[call:get_id].[name] * [amount]", callables = {"get_id": [get_id, {"items": fh.items}]})
	other_s = "空" if (other_s == "") else other_s
	mes.extend(other_s.split("\n"))
	mes.extend([LINE, "物品前数字为物品id", "发送“售卖 [物品id] [数量]”来售卖农作物"])
	await Putil.sending(bot, event)
	await Putil.reply(storage, event, MessageSegment.image(ImageUtil.text_to_image(mes, None, qq = event.user_id)))

@shop.handle()
async def _(bot: Bot, event: Event):
	await Putil.processing(bot, event)
	data = DataFile("[DATA]/farm/data")
	shop_data = data.get_raw("shop.json")
	seed_data = data.get_raw("crop.json")
	mes = ["🌱农场商店🌱", LINE, "- 种子"]
	seed_items = [x for x in list(seed_data.items()) if (x[1].get("seed_cost", None) != None)]
	items = [[f"[{list(seed_data.keys()).index(key)}]{key}种子 | {value["seed_cost"]}🦌币" for key, value in seed_items], [f"[{list(shop_data.keys()).index(key) + len(seed_items)}]{key} | {value}🦌币" for key, value in shop_data.items()]]
	items[0] = ["空~"] if (items[0] == []) else items[0]
	items[1] = ["空~"] if (items[1] == []) else items[1]
	mes.extend(items[0])
	mes.extend([LINE, "- 杂货"])
	mes.extend(items[1])
	mes.extend([LINE, "商品前数字为商品id", "发送“农场购买 [商品id] [数量]”进行购买"])
	await Putil.sending(bot, event)
	await Putil.reply(shop, event, MessageSegment.image(ImageUtil.text_to_image(mes, None, qq = event.user_id)))

@shop_buy.handle()
async def _(event: Event, args = RegexGroup()):
	shop_data = DataFile("[DATA]/farm/data").get_raw("shop.json")
	seed_data = DataFile("[DATA]/farm/data").get_raw("crop.json")
	user_data = DataFile(f"[data]/user/{event.user_id}", Logger(f"[data]/user/{event.user_id}/log/coin.log", "农场商店"))
	fh = Item(f"[data]/user/{event.user_id}/farm/storage.json")
	items = [[f"{key}种子", value["seed_cost"], "seed"] for key, value in seed_data.items() if (value.get("seed_cost", None) != None)] + [[key, value, "other"] for key, value in shop_data.items()]
	index = int(args[0])
	amount = int(args[1])
	if (amount > 0):
		if (0 <= index and index < len(items)):
			item = items[index]
			if (user_data.remove_num("profile", "coin", item[1] * amount)):
				fh.add(item[0], amount, {"type": item[2]})
				await Putil.reply(shop_buy, event, f"购买成功！\n{item[0]} * {amount} 已收入仓库")
			else:
				await Putil.reply(shop_buy, event, f"需要{item[1] * amount}🦌币！")
		else:
			await Putil.reply(shop_buy, event, "商品不存在！")
	else:
		await Putil.reply(shop_buy, event, "何意味")

@plant.handle()
async def _(event: Event, args = RegexGroup()):
	args = list(args)
	user_data = DataFile(f"[data]/user/{event.user_id}/farm")
	land = Farmland(user_data.get("farmland.json", "farmland", [{}] * 3), [user_data, "farmland.json", "farmland"])
	x, y = int(args[0]), int(args[1])
	args[2] = args[2].split("种子")[0]
	fh = Item(f"[data]/user/{event.user_id}/farm/storage.json")
	if (fh.find(f"{args[2]}种子")[1] != None):
		result = land.plant(x, y, args[2], is_save = False)
		if (result == "Done"):
			if (check_work_time(user_data, 10)):
				async def time_plant():
					land.save()
					fh.reduce(f"{args[2]}种子", 1)
					await Putil.reply(plant, event, "播种成功！")
				await Putil.reply(plant, event, "播种中...(10s)")
				delay_job(time_plant, 10)
			else:
				await Putil.reply(plant, event, "正在做别的事情！")
		elif (result == "Not In"):
			await Putil.reply(plant, event, "坐标错误！")
		elif (result == "Not Found"):
			await Putil.reply(plant, event, "种子不存在！")
		elif (result == "Not Empty"):
			await Putil.reply(plant, event, "这块地上还有作物！")
	else:
		await Putil.reply(plant, event, f"仓库里没有“{args[2]}”的种子！")

@water.handle()
async def _(event: Event, args = RegexGroup()):
	user_data = DataFile(f"[data]/user/{event.user_id}/farm")
	land = Farmland(user_data.get("farmland.json", "farmland", [{}] * 3), [user_data, "farmland.json", "farmland"])
	x, y = int(args[0]), int(args[1])
	result = land.water(x, y, is_save = False)
	if (result == "Done"):
		if (check_work_time(user_data, 5)):
			async def time_water():
				land.save()
				await Putil.reply(water, event, "浇水成功！")
			await Putil.reply(water, event, "浇水中...(5s)")
			delay_job(time_water, 5)
		else:
			await Putil.reply(water, event, "正在做别的事情！")
	elif (result == "Not In"):
		await Putil.reply(water, event, "坐标错误！")
	elif (result == "Not Dry"):
		await Putil.reply(water, event, "你已经浇过水啦~")
	elif (result == "Can Not"):
		await Putil.reply(water, event, "没啥好浇水的~")

@uproot.handle()
async def _(event: Event, args = RegexGroup()):
	user_data = DataFile(f"[data]/user/{event.user_id}/farm")
	land = Farmland(user_data.get("farmland.json", "farmland", [{}] * 3), [user_data, "farmland.json", "farmland"])
	x, y = int(args[0]), int(args[1])
	state = land.uproot(x, y, is_save = False)
	if (state == "Done"):
		if (check_work_time(user_data, 10)):
			async def time_uproot():
				land.save()
				await Putil.reply(uproot, event, "成功铲除！")
			await Putil.reply(uproot, event, "铲除中...(10s)")
			delay_job(time_uproot, 10)
		else:
			await Putil.reply(uproot, event, "正在做别的事情！")
	elif (state == "Can Not"):
		await Putil.reply(uproot, event, "这块地是空的！")
	elif (state == "Not In"):
		await Putil.reply(uproot, event, "坐标错误！")

@fertilize.handle()
async def _(event: Event, args = RegexGroup()):
	user_data = DataFile(f"[data]/user/{event.user_id}/farm")
	land = Farmland(user_data.get("farmland.json", "farmland", [{}] * 3), [user_data, "farmland.json", "farmland"])
	x, y, amount = int(args[0]), int(args[1]), int(args[2])
	fh = Item(f"[data]/user/{event.user_id}/farm/storage.json")
	if (fh.find("肥料")[1] != None):
		if (fh.reduce("肥料", amount) != "Not"):
			result = land.fertilize(x, y, amount, is_save = False)
			if (result == "Done"):
				if (check_work_time(5 * amount)):
					async def time_fertilize():
						land.save()
						await Putil.reply(fertilize, event, "施肥成功！")
					await Putil.reply(fertilize, event, f"施肥中...({5 * amount}s)")
					delay_job(time_fertilize, 5 * amount)
				else:
					await Putil.reply(fertilize, event, "正在进行别的行动！")
			elif (result == "Not In"):
				await Putil.reply(fertilize, event, "坐标错误！")
		else:
			await Putil.reply(fertilize, event, "肥料不足！")
	else:
		await Putil.reply(fertilize, event, "仓库里没有肥料！")

@harvest.handle()
async def _(event: Event, args = RegexGroup()):
	user_data = DataFile(f"[data]/user/{event.user_id}/farm")
	land = Farmland(user_data.get("farmland.json", "farmland", [{}] * 3), [user_data, "farmland.json", "farmland"])
	x, y = int(args[0]), int(args[1])
	fh = Item(f"[data]/user/{event.user_id}/farm/storage.json")
	result = land.harvest(x, y, is_save = False)
	if (result == "Not In"):
		await Putil.reply(harvest, event, "坐标错误！")
	elif (result == "Can Not"):
		await Putil.reply(harvest, event, "没有成熟的作物！")
	else:
		if (check_work_time(user_data, 5)):
			async def time_harvest():
				land.save()
				fh.add_by_list(result)
				mes = ["收获成功！", LINE]
				for item in result:
					mes.append(f"✅【{get_star(item["data"]["star"])}】{item["name"]} * {item["amount"]}")
				mes.extend([LINE, "已收入仓库！"])
				await Putil.reply(harvest, event, "\n".join(mes))
			await Putil.reply(harvest, event, f"收获中...(5s)")
			delay_job(time_harvest, 5)
		else:
			await Putil.reply(harvest, event, "正在进行别的行动！")

@sell.handle()
async def _(event: Event, args = RegexGroup()):
	fh = Item(f"[data]/user/{event.user_id}/farm/storage.json")
	index, amount = int(args[0]), int(args[1])
	if (0 <= index and index < len(fh.items)):
		user_data = DataFile(f"[data]/user/{event.user_id}", Logger(f"[data]/user/{event.user_id}/log/coin.log", "农场|售卖农作物"))
		item = fh.items[index]
		if (item["data"]["type"] == "crop"):
			if (fh.reduce(item["name"], amount, item["data"]) != "Not"):
				price = get_crop_price(item["name"], item["data"]["star"])
				user_data.add_num("profile", "coin", price * amount)
				await Putil.reply(sell, event, f"""
售卖成功！
[{get_star(item["data"]["star"])}]{item["name"]}
收入：{price} * {amount} = {price * amount}🦌币
""".strip())
			else:
				await Putil.reply(sell, event, "数量不足！")
		else:
			await Putil.reply(sell, event, "只能售卖农作物哦！")
	else:
		await Putil.reply(sell, event, "物品id错误！")

@batch_plant.handle()
async def _(event: Event, args = RegexGroup()):
	await batch_action(batch_plant, event, args, 
		action_func = "plant",
		error_text = {"Not In": "坐标错误！", "Not Found": "种子不存在！", "Not Empty": "这块地不是空的！"},
		action_name = "播种",
		delay = 10
	)

@batch_water.handle()
async def _(event: Event, args = RegexGroup()):
	await batch_action(batch_water, event, args, 
		action_func = "water",
		error_text = {"Not In": "坐标错误！", "Not Dry": "你已经浇过水啦~", "Can Not": "没什么好浇水的~"},
		action_name = "浇水",
		delay = 5
	)

@batch_uproot.handle()
async def _(event: Event, args = RegexGroup()):
	await batch_action(batch_uproot, event, args, 
		action_func = "uproot",
		error_text = {"Not In": "坐标错误！", "Can Not": "这块地是空的！"},
		action_name = "铲除",
		delay = 10
	)

@batch_fertilize.handle()
async def _(event: Event, args = RegexGroup()):
	await batch_action(batch_fertilize, event, args, 
		action_func = "fertilize",
		error_text = {"Not In": "坐标错误！"},
		action_name = "施肥",
		delay = 10
	)

@batch_harvest.handle()
async def _(event: Event, args = RegexGroup()):
	await batch_action(batch_harvest, event, args, 
		action_func = "harvest",
		error_text = {"Not In": "坐标错误！", "Can Not": "没有成熟的作物！"},
		action_name = "收获",
		delay = 5
	)

@befree.handle()
async def _(event: Event):
	user_data = DataFile(f"[data]/user/{event.user_id}/farm")
	if (user_data.get("info.json", "free", True) == False):
		work_time = user_data.get("info.json", "work_time", format_datetime(datetime.datetime.now()))
		work_time = to_datetime(work_time)
		if (work_time <= datetime.datetime.now()):
			user_data.set("info.json", "free", True)
			await Putil.reply(befree, event, "OK了！")
		else:
			await Putil.reply(befree, event, f"根据历史记录，上次行动的截止时间是{format_datetime(work_time)}")
	else:
		await Putil.reply(befree, event, "没问题啊？")

@batch_sell.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	await Putil.processing(bot, event)
	args = [Util.multi_split(x, [",", "，", "/", "+", "-", "*", "."]) for x in args[0].strip().split(" ")]
	args.sort(key = lambda x: x[0], reverse = True)
	result = {"success": 0, "failed": 0}
	error = []
	success = []
	def add_error(text):
		result["failed"] += 1
		error.append(f"❗{text}")
	def add_success(text):
		result["success"] += 1
		error.append(f"✅{text}")
	fh = Item(f"[data]/user/{event.user_id}/farm/storage.json")
	for arg in args:
		index, amount = int(arg[0]), int(arg[1])
		if (0 <= index and index < len(fh.items)):
			user_data = DataFile(f"[data]/user/{event.user_id}", Logger(f"[data]/user/{event.user_id}/log/coin.log", "农场|售卖农作物"))
			item = fh.items[index]
			if (item["data"]["type"] == "crop"):
				if (fh.reduce(item["name"], amount, item["data"]) != "Not"):
					price = get_crop_price(item["name"], item["data"]["star"])
					user_data.add_num("profile", "coin", price * amount)
					add_success(f"[{get_star(item["data"]["star"])}]{item["name"]} ==> {price} * {amount} = {price * amount}🦌币")
				else:
					add_error("数量不足！")
			else:
				add_error("只能售卖农作物哦！")
		else:
			add_error("物品id错误！")
	await Putil.sending(bot, event)
	mes = ["💰批量售卖结果💰", LINE, f"成功：{result["success"]}次", f"失败：{result["failed"]}次", LINE] + success + [LINE] + error
	await Putil.reply(batch_sell, event, MessageSegment.image(ImageUtil.text_to_image(mes, width = None, qq = event.user_id)))

async def batch_action(matcher, event, args, action_func, error_text, delay, action_name):
	args = list(args)
	user_data = DataFile(f"[data]/user/{event.user_id}/farm")
	land = Farmland(user_data.get("farmland.json", "farmland", [{}] * 3), [user_data, "farmland.json", "farmland"])
	if (action_func == "plant"):
		seed_name = args.pop(-1).split("种子")[0]
	elif (action_func == "fertilize"):
		amount = int(args[-1])
	args = [int(x) for x in args]
	begin = [min(args[0], args[2]), min(args[1], args[3])]
	end = [max(args[0], args[2]), max(args[1], args[3])]
	fh = Item(f"[data]/user/{event.user_id}/farm/storage.json")
	if (land.is_in_area(*begin) and land.is_in_area(*end)):
		result = {"success": 0, "failed": 0}
		error = []
		def add_error(x, y, text):
			result["failed"] += 1
			error.append(f"❗耕地({x},{y}) --> {text}")
		def action():
			items = []
			for y in range(end[1] - begin[1] + 1):
				for x in range(end[0] - begin[0] + 1):
					pos = [begin[0] + x, begin[1] + y]

					if (action_func not in ["plant", "fertilize"] or \
						(action_func == "plant" and fh.find(f"{seed_name}种子")[1] != None) or \
						(action_func == "fertilize" and fh.find("肥料")[1] != None and fh.find("肥料")[1]["amount"] >= amount)):
						if (action_func == "plant"):
							state = land.plant(x, y, seed_name, is_save = False)
						elif (action_func == "fertilize"):
							state = land.fertilize(x, y, amount, is_save = False)
						elif (action_func == "harvest"):
							state = land.harvest(x, y, is_save = False)
							if (type(state) == list):
								for item in state:
									items = Item.value_add(items, **item)
								state = "Done"
						else:
							state = getattr(land, action_func)(x, y, is_save = False)
						if (state == "Done"):
							if (action_func == "plant"):
								fh.reduce(f"{seed_name}种子", 1)
							elif (action_func == "fertilize"):
								fh.reduce("肥料", amount)
							result["success"] += 1
						else:
							add_error(x, y, error_text[state])
					else:
						if (action_func == "plant"):
							add_error(x, y, "种子不足！")
						elif (action_func == "fertilize"):
							add_error(x, y, "肥料不足！")
						return
			result["items"] = items
		action()
		delay = delay * result["success"]
		if (action_func == "fertilize"):
			delay *= amount

		if (check_work_time(user_data, delay)):
			await Putil.reply(matcher, event, f"{action_name}中...({delay}s)")
			async def time_batch():
				fh.add_by_list(result.get("items", []))
				land.save()
				mes = [f"🌱批量{action_name}结果🌱", LINE, f"成功：{result["success"]}次", f"失败：{result["failed"]}次", LINE]
				if (action_func == "harvest"):
					mes.append("🎉收获成果：")
					for item in result.get("items", []):
						mes.append(f"【{get_star(item["data"]["star"])}】{item["name"]} * {item["amount"]}")
					mes.append(LINE)
				mes.extend(error)
				await Putil.reply(matcher, event, MessageSegment.image(ImageUtil.text_to_image(mes, width = None, qq = event.user_id)))
			delay_job(time_batch, delay)
		else:
			await Putil.reply(matcher, event, "正在进行别的行动！")
	else:
		await Putil.reply(matcher, event, "范围过大！")

class Farmland: #耕地类
	"""
	self.land传入时为一维列表，后自动转换为二维列表，存储每块地的信息
	数据格式：
	{
		"state": "str", #状态 --> dry | wet
		"crop": "str", #种植的作物名(资源名)
		"display_name": "str", #种植的作物的名称，为了方便寻找
		"plant_time": "xxxx-xx-xx xx:xx:xx", #种植的时间
		"grow_time": xx, #生长所需要的时间(分钟)，应不变
		"water_time": [[], [], ..], #一个嵌套列表，储存[浇水的时间, 浇水的有效截止期]
		"growth": int #作物已生长的时间(分钟)，由"water_time"计算(截止期-浇水时间),
		"fertilizer": [int, str, str] #储存肥料相关信息，[肥力值，上次消耗肥料的时间]
		"add_growth" int #因肥料等因素增加的
	}
	"""
	def __init__(self, lands: list, datafile = None):
		self.land = lands
		self.width = 0
		self.height = 0
		self.datafile = datafile
		self.shape()
		
		for y in range(self.height):
			for x in range(self.width):
				fdata = self.land[y][x]
				if (fdata == None):
					continue
				if (fdata.get("crop", None) != None):
					#根据浇水时间计算每块地作物的生长时间
					growth = 0
					water_time = fdata.get("water_time", [])
					dtime = datetime.datetime.now()
					for start, end in water_time:
						start = to_datetime(start)
						end = to_datetime(end)
						end = min(end, dtime)
						growth += (end - start).total_seconds()
					growth /= 60

					#计算肥力值
					fertilizer = fdata.get("fertilizer", [0, None])
					if (fertilizer[0] > 0):
						last_time = to_datetime(fertilizer[1])
						consume = min(fertilizer[0], (dtime - last_time).total_seconds() / 60)
						self.land[y][x]["fertilizer"][0] -= consume
						self.land[y][x]["add_growth"] = fdata.get("add_growth", 0) + consume
						self.land[y][x]["fertilizer"][1] = format_datetime(dtime)
						if (self.land[y][x]["fertilizer"][0] <= 0):
							self.land[y][x]["fertilizer"] = [0, None]

					fdata = self.land[y][x]
					growth += fdata.get("add_growth", 0)
					self.land[y][x]["growth"] = growth

					#判断干湿及是否枯萎
					delta = to_datetime(water_time[-1][1] if (len(water_time) > 0) else fdata["plant_time"]) - dtime
					if (delta < datetime.timedelta(0)):
						self.land[y][x]["state"] = "dry"
						crop_data = DataFile("[DATA]/farm/data").get_raw("crop.json").get(fdata["display_name"], None)
						wilt = crop_data.get("wilt", None)
						if (wilt != None and abs(delta).total_seconds() > wilt * 60 * 60):
							land_data = {
								"state": "dry",
								"crop": "wilt",
								"display_name": "枯枯",
								"plant_time": format_datetime(dtime),
								"grow_time": 0.1,
								"water_time": [],
								"growth": 0
							}
							self.land[y][x] = land_data
					
		self.save()

	def save(self):
		if (self.datafile != None):
			self.datafile[0].set(self.datafile[1], self.datafile[2], self.get_flatten())
			return True
		else:
			return False

	def shape(self, width = "auto"):
		if (width == "auto"):
			self.height = math.floor(math.sqrt(len(self.land)))
		self.width = math.ceil(len(self.land) / self.height)
		#填充空值
		arr = np.array(self.land + [None] * (self.width * self.height - len(self.land)))
		self.land = arr.reshape(self.height, self.width).tolist()
	
	def get_flatten(self):
		return np.array(self.land).flatten().tolist()

	def get_image(self, time, in_bytes = True):
		#根据时间设置天空亮度
		noon = time.combine(date = time.date(), time = datetime.time(12, 0, 0))
		percent = int((1 - (abs(time - noon).total_seconds() / 43200)) * 100)
		img = Image.new("RGBA", (self.width * 32, self.height * 32 + 64), f"hsv(200,50%,{percent}%)")

		#添加太阳/月亮
		if (time.hour >= 6 and time.hour < 18):
			i = get_src("Sun")
			p = (time - time.combine(date = time.date(), time = datetime.time(6, 0, 0))) / datetime.timedelta(hours = 12)
			loc = round(self.width * 32 * p)
		else:
			i = get_src("Moon")
			p = (time - time.combine(date = time.date(), time = datetime.time(18, 0, 0)).replace(day = time.day if (time.hour >= 18) else time.day - 1)) / datetime.timedelta(hours = 12)
			loc = round(self.width * 32 * p)
		img.paste(i, (loc - 16, 8), i)
		font = ImageFont.truetype(DataFile("[DATA]/font").get_path(f"Pixel12px.ttf"), size = 20)
		for y in range(self.height):
			for x in range(self.width):
				pos = (x * 32, y * 32 + 64)
				fdata = self.land[y][x]
				if (fdata == None):
					img.paste(get_src("farmland_locked"), pos)
					continue
				img.paste(get_src("farmland_wet" if (fdata.get("state", "dry") == "wet") else "farmland_dry"), pos)
				if (fdata.get("crop", None) != None): #作物
					plant_time = to_datetime(fdata["plant_time"])
					crop_data = DataFile("[DATA]/farm/data").get_raw("crop.json").get(fdata["display_name"])
					total_stage = crop_data["stage"]

					#根据时间差计算作物生长阶段
					i = min(1, fdata["growth"] / fdata["grow_time"])
					current_stage = math.floor((total_stage - 1) * i)
					crop = get_src(f"crop/{fdata["crop"]}/{fdata["crop"]}_{current_stage}")

					#特殊形态
					for cond in crop_data.get("special_stage", []):
						if (self.check_condition(x, y, cond["condition"])):
							crop = get_src(f"crop/{fdata["crop"]}/{fdata["crop"]}_{cond["src"]}")

					#打印
					layer = Image.new("RGBA", (img.size[0], img.size[1]), (0, 0, 0, 0))
					layer.paste(crop, pos, mask = crop)
					img = Image.alpha_composite(img, layer)

		img = img.resize((img.size[0] * 8, img.size[1] * 8), Image.Resampling.NEAREST)
		#打印编号及肥力值
		num_img = Image.new("RGBA", (img.size[0], img.size[1]), (0, 0, 0, 0)) #ImageDraw.text如果颜色带alpha居然不能直接叠加，还要新建个图像，哎，真tm麻烦
		draw = Pilmoji(num_img)
		for y in range(self.height):
			for x in range(self.width):
				pos = [x * (32 * 8) + 8, y * (32 * 8) + (64 * 8) + 4]
				fdata = self.land[y][x]
				if (fdata == None):
					continue
				text = f"({x},{y}) 肥力值:{round(fdata.get("fertilizer", [0, None])[0], 2)}"
				draw.text(xy = pos, text = text, fill = (255, 255, 255, 150), font = font, stroke_width = 2, stroke_fill = (0, 0, 0, 150))
				if (fdata.get("crop", None) != None):
					symbol = {"dry": "⛔", "wet": "↑"}[fdata["state"]] if (self.get_state(x, y) != "Mature") else "✅"
					text = f"[{fdata["display_name"]}] {round(min(1, fdata["growth"] / fdata["grow_time"]) * 100, 2)}% {symbol}"

					#肥料生长图标
					if (fdata.get("fertilizer", [0, None])[0] > 0):
						text += "↑"

					#缺水图标（离枯死期限还有一半时间）
					delta = to_datetime(fdata["water_time"][-1][1] if (len(fdata["water_time"]) > 0) else fdata["plant_time"]) - time
					if (delta < datetime.timedelta(0)):
						crop_data = DataFile("[DATA]/farm/data").get_raw("crop.json").get(fdata["display_name"], None)
						wilt = crop_data.get("wilt", None)
						if (wilt != None and abs(delta).total_seconds() > (wilt * 60 * 60 / 2)):
							text += "💧"

					pos[1] += font.getbbox("汉字")[3]
					draw.text(xy = pos, text = text, fill = (255, 255, 255, 150), font = font, stroke_width = 2, stroke_fill = (0, 0, 0, 150))
		img = Image.alpha_composite(img, num_img)
		return ImageUtil.img_to_bytesio(img) if (in_bytes) else img

	def is_in(self, x, y):
		try:
			land = self.land[y][x]
			return land != None
		except Exception:
			return False

	def is_in_area(self, x, y):
		try:
			self.land[y][x]
			return True
		except Exception:
			return False

	def get_state(self, x, y):
		if (self.is_in(x, y)):
			land = self.land[y][x]
			if (land.get("crop", None) != None):
				plant_time = to_datetime(land["plant_time"])
				if (land["growth"] >= land["grow_time"]):
					return "Mature"
				else:
					return "Growing"
			else:
				return "Empty"
		else:
			return "Not In"

	def set(self, x, y, data, is_save = True):
		self.land[y][x] = data
		if (is_save):
			self.save()

	def get(self, x, y, data_name = None, default = None):
		return self.land[y][x] if (data_name == None) else self.land[y][x].get(data_name, default)

	def plant(self, x, y, name, is_save = True):
		time = datetime.datetime.now()
		if (self.is_in(x, y)):
			land = self.land[y][x]
			crop_data = DataFile("[DATA]/farm/data").get_raw("crop.json").get(name, None)
			if (crop_data != None):
				if (self.get_state(x, y) == "Empty"):
					land_data = {
						"state": land.get("state", "dry"),
						"crop": crop_data.get("name", name),
						"display_name": name,
						"plant_time": format_datetime(time),
						"grow_time": crop_data.get("grow_time", None),
						"water_time": [],
						"growth": 0,
						"fertilizer": [land.get("fertilizer", [0, None])[0], format_datetime(time) if (land.get("fertilizer", [0, None])[0] != 0) else None],
						"add_growth": 0
					}
					self.set(x, y, land_data, is_save)
					return "Done"
				else:
					return "Not Empty"
			else:
				return "Not Found"
		else:
			return "Not In"

	def water(self, x, y, is_save = True):
		time = datetime.datetime.now()
		if (self.is_in(x, y)):
			land = self.land[y][x]
			if (self.get_state(x, y) in ["Mature", "Growing"]):
				if (land["state"] == "dry"):
					crop_data = DataFile("[DATA]/farm/data").get_raw("crop.json").get(land["display_name"], None)
					self.land[y][x]["state"] = "wet"
					end = time + datetime.timedelta(minutes = crop_data["water_time"])
					self.land[y][x]["water_time"].append([format_datetime(time), format_datetime(end)])
					if (is_save):
						self.save()
					return "Done"
				else:
					return "Not Dry"
			else:
				return "Can Not"
		else:
			return "Not In"

	def uproot(self, x, y, is_save = True):
		time = datetime.datetime.now()
		if (self.is_in(x, y)):
			land = self.land[y][x]
			if (self.get_state(x, y) in ["Mature", "Growing"]):
				self.set(x, y, {
					"fertilizer": [self.get(x, y, "fertilizer", [0, None])[0], None]
				}, is_save)
				return "Done"
			else:
				return "Can Not"
		else:
			return "Not In"

	def fertilize(self, x, y, value, is_save = True):
		time = datetime.datetime.now()
		if (self.is_in(x, y)):
			land = self.land[y][x]
			fertilizer = land.get("fertilizer", [0, None])
			fertilizer[0] += value * 120
			fertilizer[1] = format_datetime(time) if (fertilizer[1] == None and self.get(x, y, "crop", None) != None) else fertilizer[1]
			self.land[y][x]["fertilizer"] = fertilizer
			if (is_save == True):
				self.save()
			return "Done"
		else:
			return "Not In"

	def harvest(self, x, y, is_save = True):
		if (self.is_in(x, y)):
			land = self.land[y][x]
			if (self.get_state(x, y) == "Mature"):
				crop_data = DataFile("[DATA]/farm/data").get_raw("crop.json").get(land["display_name"], None)

				name = land["display_name"]
				amount = [0, 0]
				star = [0, 0]

				for expr in crop_data["harvest"]:
					cond = expr["condition"]
					if (self.check_condition(x, y, cond)):
						ex_type =  expr.get("type", "set")
						if (ex_type == "set"):
							amount = expr.get("amount", amount)
							star = expr.get("star", star)
						else:
							amount = [x + y for x, y in zip(expr.get("amount", [0, 0]), amount)]
							star = [x + y for x, y in zip(expr.get("star", [0, 0]), star)]
						name = expr.get("name", name)

				items = []
				amount = random.randint(amount[0], amount[1]) if (type(amount) == list) else amount
				for i in range(amount):
					items = Item.value_add(items, name, 1, {
						"type": "crop",
						"star": random.randint(star[0], star[1]) if (type(star) == list) else star
					})
				print("harvest:", items)
				self.uproot(x, y, is_save)
				return items
			else:
				return "Can Not"
		else:
			return "Not In"

	def check_condition(self, x, y, condition):
		if (self.is_in(x, y)):
			land = self.land[y][x]
			result = []
			if (condition == None):
				return True
			for cond in condition:
				cond = cond.split(" ")
				for i in range(len(cond)):
					token = cond[i]
					if (token == "growth"):
						cond[i] = land.get("growth", 0)
					elif (token == "add_growth"):
						cond[i] = land.get("add_growth", 0)
					elif (token == "water_period"):
						value = 0
						last = None
						for start, end in land.get("water_time", []):
							if (last != None):	
								start = to_datetime(start)
								period = (start - last).total_seconds() / 60
								value = min(value, period) if (value > 0) else period
							last = to_datetime(end)
						cond[i] = value
					elif (token == "water_times"):
						cond[i] = len(land.get("water_time", []))
				result.append(eval("".join([str(x) for x in cond]), {"__builtins__": None}, {}))
			return all(result)
		else:
			return "Not In"

def get_crop_price(crop_name, star):
	crop_data = DataFile("[DATA]/farm/data").get_raw("crop.json")
	prices = [value["price"] if (type(value["price"]) == dict) else {name: value["price"]} for name, value in crop_data.items()]
	all_price = dict()
	for price in prices:
		all_price.update(price)
	if (crop_name in all_price):
		return round(all_price[crop_name] * (1 + star * 0.5))
	else:
		return None

def get_src(spath):
	return Image.open(os.path.join(src_path, f"{spath}.png")).convert("RGBA")

def get_id(item, items):
	return items.index(item)

def get_star(num):
	return "★" * num if (num > 0) else "普通"

def to_datetime(string):
	return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def format_datetime(dtime):
	return dtime.strftime("%Y-%m-%d %H:%M:%S")

def delay_job(func, seconds):
	scheduler.add_job(func, "date", run_date = datetime.datetime.now() + datetime.timedelta(seconds = seconds))

def check_work_time(udata, delay):
	work_time = udata.get("info.json", "work_time", None)
	dtime = datetime.datetime.now()
	if (work_time == None or to_datetime(work_time) <= dtime):
		udata.set("info.json", "work_time", format_datetime(dtime + datetime.timedelta(seconds = delay)))
		return True
	else:
		return False