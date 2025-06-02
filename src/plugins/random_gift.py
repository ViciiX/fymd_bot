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
first_time = True

code_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

async def summon_code():
	global first_time
	dtime = datetime.datetime.now()
	next_time = get_normal_random(10, 200, 1, 0)[0] * 60

	if (first_time == False):
		avr_coin = next_time/60
		coin = int(get_normal_random(avr_coin/2, avr_coin*2, 1)[0])
		user = random.randint(1, 4)
		time = random.randint(40, 70)
		deadline = (dtime + datetime.timedelta(seconds = time)).strftime("%Y-%m-%d %H:%M:%S")
		code = "".join([code_chars[random.randint(0, 35)] for x in range(16)])
		add_code(code, round(coin / user), deadline, user, "✨活跃奖励✨", True)
		mes = ["🎁神秘兑换码出现❗", f"⏰限时时间：{time}秒内！", f"😸数量：{user}", f"🎇兑换码：{code}"]
		await bot.send_group_msg(group_id = group_id, message = "\n".join(mes))
	else:
		first_time = False

	run_time = dtime + datetime.timedelta(seconds = next_time)
	print(f"wait_time --> {next_time/60}min")
	scheduler.add_job(summon_code, "date", run_date = run_time)

def add_code(name, amount, deadline, count, text, temp):
	code = locals()
	del code["name"]
	DataFile(f"[data]").set("gift_code.json", name, code)

def get_fymd_bot():
	global bot
	bots = get_bots()
	if (bots != {}):
		print("I got bot")
		bot = bots[str(bot_id)]
		scheduler.add_job(summon_code, "date", run_date = datetime.datetime.now())
	else:
		scheduler.add_job(get_fymd_bot, "date", run_date = datetime.datetime.now() + datetime.timedelta(seconds = 3))

def get_normal_random(_min, _max, count = 1, round_num = 0, scale = 0.25):
	mean = (_min + _max) / 2
	std_dev = (_max - _min) * scale
	random_numbers = np.random.normal(mean, std_dev, 100 + count)
	random_numbers = np.clip(random_numbers, _min, _max)
	return np.random.choice(np.round(random_numbers, round_num), count, replace = True).tolist()

scheduler.add_job(get_fymd_bot, "date", run_date = datetime.datetime.now() + datetime.timedelta(seconds = 3))