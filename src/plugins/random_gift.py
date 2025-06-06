import datetime, os, random
import numpy as np

from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot import require, on_fullmatch, get_bots
from ..utils.file import DataFile
from ..utils import util as Util
from nonebot.permission import SUPERUSER

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

group_id = 962905095
bot_id = 1415821084

bot = None

code_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

drop_it = on_fullmatch("#drop", permission = SUPERUSER)

@drop_it.handle()
async def _():
	await summon_code()
	await drop_it.finish("Dropped it")

async def main_loop():
	data = DataFile("[data]")
	dtime = datetime.datetime.now()
	time = data.get("random_gift.json", "next_time", dtime.strftime("%Y-%m-%d %H:%M:%S"))
	time = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
	if (time < dtime):
		next_time = await summon_code()
		data.set("random_gift.json", "next_time", next_time.strftime("%Y-%m-%d %H:%M:%S"))

async def summon_code():
	dtime = datetime.datetime.now()
	next_time = get_normal_random(10, 180, 1, 0)[0] * 60

	avr_coin = next_time/60
	coin = int(get_normal_random(avr_coin/2, avr_coin*2, 1)[0])
	user = random.randint(1, 4)
	time = random.randint(10, 30)
	deadline = (dtime + datetime.timedelta(minutes = time)).strftime("%Y-%m-%d %H:%M:%S")
	code = "".join([code_chars[random.randint(0, 35)] for x in range(16)])
	add_code(code, round(coin / user), deadline, user, "✨活跃奖励✨", True)
	mes = ["🎁神秘兑换码出现❗", f"⏰限时时间：{time}分钟内！", f"😸数量：{user}", f"🎇兑换码：{code}"]
	await bot.send_group_msg(group_id = group_id, message = "\n".join(mes))

	run_time = dtime + datetime.timedelta(seconds = next_time)
	return run_time

def add_code(name, amount, deadline, count, text, temp):
	code = locals()
	data = DataFile(f"[data]")
	del code["name"]
	data.set("gift_code.json", name, code)
	history = data.get("gift_code_temp.json", "codes", [])
	history = set(history)
	history.add(name)
	data.set("gift_code_temp.json", "codes", list(history))

def get_fymd_bot():
	global bot
	bots = get_bots()
	if (bots != {}):
		print("I got bot")
		bot = bots[str(bot_id)]
		scheduler.add_job(main_loop, "interval", seconds = 5)
		scheduler.remove_job("get_bot")

def get_normal_random(_min, _max, count = 1, round_num = 0, scale = 0.25):
	mean = (_min + _max) / 2
	std_dev = (_max - _min) * scale
	random_numbers = np.random.normal(mean, std_dev, 100 + count)
	random_numbers = np.clip(random_numbers, _min, _max)
	return np.random.choice(np.round(random_numbers, round_num), count, replace = True).tolist()

scheduler.add_job(get_fymd_bot, "interval", seconds = 1, id = "get_bot")