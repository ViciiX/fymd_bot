from PIL import Image
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

src_path = DataFile("[DATA]/farm/src").path

myland = on_fullmatch("农场")

@myland.handle()
async def _(event: Event):
	data = DataFile(f"[data]/user/{event.user_id}/farm")
	land = Farmland(data.get("farmland.json", "farmland", [{}] * 3))
	await Putil.reply(myland, event, f"🌱🌳{event.sender.nickname} 的农场🌳🌱" + MessageSegment.image(land.get_image(datetime.datetime.now())))

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

		for y in range(self.height):
			for x in range(self.width):
				pos = (x * 32, y * 32 + 64)
				fdata = self.land[y][x]
				img.paste(get_src("farmland_wet" if (fdata.get("state", "dry") == "wet") else "farmland_dry"), pos)
				if (fdata.get("crop", None) != None): #作物
					plant_time = datetime.datetime.strptime(fdata["plant_time"], "%Y-%m-%d %H:%M:%S")
					total_stage = len(os.listdir(os.path.join(src_path, f"crop/{fdata["crop"]}")))

					#根据时间差计算作物生长阶段
					i = min(1, (abs(time - plant_time).seconds / 60) / fdata["grow_time"])
					current_stage = math.floor((total_stage - 1) * i)

					crop = get_src(f"crop/{fdata["crop"]}/{fdata["crop"]}_{current_stage}")
					img.paste(crop, pos, mask = crop)
		img = img.resize((img.size[0] * 8, img.size[1] * 8), Image.Resampling.NEAREST)
		return ImageUtil.img_to_bytesio(img) if (in_bytes) else img

def get_src(spath):
	return Image.open(os.path.join(src_path, f"{spath}.png"))