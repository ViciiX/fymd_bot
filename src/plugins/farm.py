from PIL import Image, ImageDraw, ImageFont
import numpy as np
import math, datetime, os

from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot import on_fullmatch, on_message, on_regex
from nonebot.params import RegexGroup

from ..utils.file import DataFile, Item, Logger
from ..utils import util as Util
from ..utils import plugin_util as Putil
from ..utils import image_util as ImageUtil

LINE = "——————————"
src_path = DataFile("[DATA]/farm/src").path

myland = on_fullmatch("农场")
storage = on_fullmatch("仓库")
shop = on_fullmatch("农场商店")
shop_buy = on_regex("^农场购买 (\\d+) (\\d+)$")
plant = on_regex("^种植 (\\d+) (\\d+) (.+)$")

@myland.handle()
async def _(event: Event):
	data = DataFile(f"[data]/user/{event.user_id}/farm")
	land = Farmland(data.get("farmland.json", "farmland", [{}] * 3))
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
	mes.append(LINE)
	await Putil.sending(bot, event)
	await Putil.reply(storage, event, MessageSegment.image(ImageUtil.text_to_image(mes, None, qq = event.user_id)))

@shop.handle()
async def _(bot: Bot, event: Event):
	await Putil.processing(bot, event)
	data = DataFile("[DATA]/farm/data")
	shop_data = data.get_raw("shop.json")
	seed_data = data.get_raw("crop.json")
	mes = ["🌱农场商店🌱", LINE, "- 种子"]
	items = [[f"[{list(seed_data.keys()).index(key)}]{key}种子 | {value["seed_cost"]}🦌币" for key, value in seed_data.items() if (value.get("seed_cost", None) != None)], [f"[{list(shop_data.keys()).index(key) + len(seed_data.keys())}]{key} | {value}🦌币" for key, value in shop_data.items()]]
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
async def _(event: Event):
	farm_data = DataFile(f"[data]/user/{event.user_id}/farm")
	land = Farmland(farm_data.get("farmland.json", "farmland", [{}] * 3))


class Farmland: #耕地类
	"""
	self.land为二维列表，存储每块地的信息
	数据格式：
	{
		"state": "str", #状态 --> dry | wet
		"crop": "str", #种植的作物名
		"plant_time": "xxxx-xx-xx xx:xx:xx", #种植的时间
		"grow_time": xx #生长所需要的时间(分钟)
	}
	"""
	def __init__(self, lands: list):
		self.land = lands
		self.width = 0
		self.height = 0
		self.shape()

	def shape(self, width = "auto"):
		if (width == "auto"):
			self.height = math.floor(math.sqrt(len(self.land)))
		self.width = math.ceil(len(self.land) / self.height)
		#填充空值
		arr = np.array(self.land + [{}] * (self.width * self.height - len(self.land)))
		self.land = arr.reshape(self.height, self.width).tolist()
	
	def get_image(self, time, in_bytes = True):
		#根据时间设置天空亮度
		noon = time.combine(date = time.date(), time = datetime.time(12, 0, 0))
		percent = int((1 - (abs(time - noon).seconds / 43200)) * 100)
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
		font = ImageFont.truetype(DataFile("[DATA]/font").get_path(f"Pixel12px.ttf"), size = 24)
		for y in range(self.height):
			for x in range(self.width):
				pos = (x * 32, y * 32 + 64)
				fdata = self.land[y][x]
				img.paste(get_src("farmland_wet" if (fdata.get("state", "dry") == "wet") else "farmland_dry"), pos)
				if (fdata.get("crop", None) != None): #作物
					plant_time = datetime.datetime.strptime(fdata["plant_time"], "%Y-%m-%d %H:%M:%S")
					total_stage = len(os.listdir(os.path.join(src_path, f"crop/{fdata["crop"]}")))

					#根据时间差计算作物生长阶段
					if (fdata["grow_time"] > 0):
						i = min(1, (abs(time - plant_time).seconds / 60) / fdata["grow_time"])
						current_stage = math.floor((total_stage - 1) * i)
					else:
						current_stage = total_stage - 1

					crop = get_src(f"crop/{fdata["crop"]}/{fdata["crop"]}_{current_stage}")
					img.paste(crop, pos, mask = crop)

		img = img.resize((img.size[0] * 8, img.size[1] * 8), Image.Resampling.NEAREST)
		#打印编号
		num_img = Image.new("RGBA", (img.size[0], img.size[1]), (0, 0, 0, 0)) #ImageDraw.text如果颜色带alpha居然不能直接叠加，还要新建个图像，哎，真tm麻烦
		draw = ImageDraw.Draw(num_img)
		for y in range(self.height):
			for x in range(self.width):
				pos = (x * 32 * 8 + 16, y * 32 * 8 + 64 * 8 + 16)
				draw.text(xy = pos, text = f"({x},{y})", fill = (255, 255, 255, 200), font = font)
		img = Image.alpha_composite(img, num_img)
		return ImageUtil.img_to_bytesio(img) if (in_bytes) else img

	def is_in(x, y):
		try:
			self.land[y][x]
			return True
		except Exception:
			return False

	def get_state(x, y):
		if (self.is_in(x, y)):
			land = self.land[y][x]
			if (land.get("crop", None) != None):
				plant_time = datetime.datetime.strptime(land["plant_time"], "%Y-%m-%d %H:%M:%S")
				if ((plant_time + datetime.timedelta(minutes = land["grow_time"])) <= datetime.datetime.now()):
					return "Mature"
				else:
					return "Growing"
			else:
				return "Empty"
		else:
			return "Not In"

	def plant(x, y, name, time):
		if (self.is_in(x, y)):
			land = self.land[y][x]
			crop_data = DataFile("[DATA]/farm/data").get_raw("crop.json").get(name, None)
			if (crop_data != None):
				if (self.get_state(x, y) == "Empty"):
					land_data = {
						"state": land.get("state", "dry"),
						"crop": name,
						"plant_time": time.strftime("%Y-%m-%d %H:%M:%S"),
						"grow_time": crop_data.get("grow_time", None)
					}
					self.land[y][x] = land_data
					return "Done"
				else:
					return "Not Empty"
			else:
				return "Not Found"
		else:
			return "Not In"

def get_src(spath):
	return Image.open(os.path.join(src_path, f"{spath}.png"))

def get_id(item, items):
	return items.index(item)

def get_star(num):
	return "★" * num