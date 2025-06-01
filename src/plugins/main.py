import random, os, pickle
import datetime, calendar, json

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot import on_fullmatch, on_message, on_regex
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.exception import AdapterException
from nonebot.params import RegexGroup
from nonebot.adapters.onebot.v11.event import GroupMessageEvent

from ..utils.file import DataFile
from ..utils import util as Util
from ..utils import plugin_util as Putil

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
bot_id = Putil.bot_id

#写入刚开始运行的时间
runtime = DataFile("[data]")
runtime.set("runtime", "time", datetime.datetime.now().timestamp())

atme = on_message(rule = to_me(), priority = 2, block = True)
impart_receive = on_message(priority = 2, block = True)

fymd = on_regex("^方悦名都$|^FYMD$")
forhelp = on_regex("^帮助 (\\d+)$|^帮助$")

sign = on_fullmatch("签到")
profile = on_fullmatch("个人面板")
rate = on_regex("^鹿 (\\d+)$")
luclock = on_fullmatch("鹿钟")
cum = on_regex("^鹿$|^🦌$", rule = to_me())
can_lu_today = on_fullmatch("今天鹿吗", rule = to_me())
advice = on_regex("^建议\n(.+)\n([\\s\\S]+)$")
subscribe_impart = on_regex("^订阅音趴$|^订阅一起听$")
unsubscribe_impart = on_regex("^取消订阅音趴$|^取消订阅一起听$")
topcoin = on_fullmatch("鹿币排行榜")
present = on_regex("^兑换码 (.+)$")

test = on_fullmatch("#test", permission = SUPERUSER)
sendsrc = on_fullmatch("#src", permission = SUPERUSER)
advice_list = on_fullmatch("#adv", permission = SUPERUSER)
show_advice = on_regex("#show (\\d+)", permission = SUPERUSER)
reply_advice = on_regex("#reply (\\d+)\n([\\s\\S]+)", permission = SUPERUSER)
add_present = on_regex("#code (.+)\namount (\\d+)\ntime (.+)\ntext ([\\s\\S]+)")

LINE = "——————————"

@test.handle()
async def _(bot: Bot, event: Event):
	pass


@sendsrc.handle()
async def _():
	path = os.path.join(os.getcwd(), "tosend")
	for file_name in os.listdir(path):
		fmt = file_name.split(".")[1]
		type_ = {"mp4": "video", "png": "image", "jpg": "image"}
		print(f"sending --> {os.path.join(path, file_name)}, type: --> {type_[fmt]}")
		await sendsrc.send(getattr(MessageSegment, type_[fmt])(os.path.join(path, file_name)))

@advice.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	data = DataFile("[data]/advice")
	dtime = datetime.datetime.now()
	content = f"昵称：{event.sender.nickname}\nQQ号：{event.user_id}\n群号：{event.group_id}\n\n{args[1].replace("🎈", "_")}"
	data.set_by_dict(f"{args[0]}🎈{dtime.timestamp()}.txt", {"user_id": event.user_id, "group_id": event.group_id, "content": content})
	await bot.send_msg(message_type = "private", user_id = 181275358, message = f"{content}")
	await Putil.reply(advice, event, "已收到！感谢你的建议！")

@advice_list.handle()
async def _():
	data = DataFile("[data]/advice")
	files = [x.split("🎈")[0] for x in data.get_files("")]
	files = [f"{i}_{files[i]}" for i in range(len(files))]
	await advice_list.finish(f"当前未处理的建议：\n{"\n- ".join(files)}")

@show_advice.handle()
async def _(bot: Bot, args = RegexGroup()):
	data = DataFile("[data]/advice")
	files = data.get_files("")
	content = data.get(files[int(args[0])], "content", "Null")
	await show_advice.finish(content)

@reply_advice.handle()
async def _(bot: Bot, args = RegexGroup()):
	data = DataFile("[data]/advice")
	files = data.get_files("")
	uid = data.get(files[int(args[0])], "user_id", None)
	gid = data.get(files[int(args[0])], "group_id", None)
	mes = MessageSegment.at(uid) + f""" 你的建议收到反馈啦！\n建议的标题：{files[int(args[0])].split("🎈")[0]}\n回复内容：{args[1]}"""
	data.delete(files[int(args[0])])
	await bot.send_group_msg(group_id = gid, message = mes)
	await reply_advice.finish("OK")

@add_present.handle()
async def _(args = RegexGroup()):
	code = {"amount": int(args[1]), "deadline": args[2] if (args[2] not in ["None", "/", " "]) else None, "text": args[3]}
	DataFile(f"[data]").set("gift_code.json", args[0], code)
	await add_present.finish(f"添加成功：{args[0]}")


@atme.handle()
async def _(bot: Bot, event: Event):
	if (isinstance(event, GroupMessageEvent)):
		dtime = datetime.datetime.now()
		start_time = runtime.get("runtime", "time", dtime.timestamp)
		start_time = datetime.datetime.fromtimestamp(start_time)
		data = DataFile("[data]")
		mes = f"""[𝕱𝖚𝖈𝖐 𝖄𝖔𝖚 𝕸𝖊𝖑𝖔𝖉𝖎𝖈 𝕯𝖚𝖇𝖘𝖙𝖊𝖕]
专属机器人 unOFFICIAL
发送“帮助”获取所有功能
————————————
✅已连续运行{Util.format_delta_time(dtime - start_time)}！
🪐已上线{Util.format_delta_time(dtime - datetime.datetime(year = 2025, month = 4, day = 16, hour = 23, minute = 9))}！
💾已存储{Util.format_file_size(sum([Util.get_dir_size(data.get_path(path)) for path in os.listdir(data.path) if (path != "DATA")]))}用户数据！"""
		await Putil.reply(atme, event, mes)

@forhelp.handle()
async def _(event: Event, args = RegexGroup()):
	if (args[0] == None):
		data = DataFile("[data]/DATA")
		help_dict = data.get("help.json", "main", {})
		text = f"""功能列表
————————————
{"\n".join([f"{i}.{list(help_dict.keys())[i]}" for i in range(len(help_dict.keys()))])}
————————————
发送“帮助 [序号]”获取详细帮助
如：帮助 2
————————————"""
		mes = Message.template("""{}
对于某些功能：
回应{}时表示正在获取/处理
回应{}时表示正在发送信息
""").format(text, MessageSegment.face(424), MessageSegment.face(124))
		await forhelp.finish(mes)
	else:
		data = DataFile("[data]/DATA")
		help_dict = data.get("help.json", "main", {})
		help_list = list(help_dict.keys())
		index = int(args[0])
		if (0 <= index and index <= len(help_list)-1):
			await Putil.reply(forhelp, event, f"""{help_list[index]}
————————————
{"\n".join(help_dict[help_list[index]])}""")
		else:
			await Putil.reply(forhelp, event, "404 Not Fucked")

@fymd.handle()
async def _(event: Event):
	await Putil.reply(fymd, event, """方悦名都
参考价格：6515 元/m²
物业类型：住宅
土地使用年限：70年
区县：锡林浩特
环线：暂无数据
街镇：锡林浩特城区
地址：锡林浩特-锡林浩特城区 宝昌路,近那达慕西街""",)

@sign.handle()
async def _(event: Event):
	data = DataFile(f"[data]/user/{event.user_id}")
	time = datetime.datetime.now()
	last_time = datetime.datetime.strptime(data.get("profile", "last_sign_time", (time-datetime.timedelta(days = 1)).strftime("%Y-%m-%d")), "%Y-%m-%d")
	if (time >= (last_time+datetime.timedelta(days = 1))):
		is_first = False
		coin = data.get("profile", "coin", 0)
		amount = random.randint(10, 20)
		group = DataFile()
		first_time = datetime.datetime.strptime(group.get("sign", "last_sign_time", (time-datetime.timedelta(days = 2)).strftime("%Y-%m-%d")), "%Y-%m-%d")
		count = group.get("sign", "count", 0)
		if (time >= (first_time+datetime.timedelta(days = 1)) or count < 3):
			group.set("sign", "last_sign_time", time.strftime("%Y-%m-%d"))
			if (time >= (first_time+datetime.timedelta(days = 1))):
				group.set("sign", "count", 1)
			else:
				group.add_num("sign", "count", 1)
			amount *= 2
			is_first = True
		else:
			group.set("sign", "count", group.get("sign", "count", 0)+1)
		data.set("profile", "last_sign_time", time.strftime("%Y-%m-%d"))
		data.set("profile", "coin", coin+amount)
		await Putil.reply(sign, event, Message.template("""{}
签到成功！
It's time to 🦌！
————————————————
你是FYMD今天第{}个签到的人！{}
🦌币+{}
当前已有🦌币：{}""").format(MessageSegment.image(os.path.join(os.getcwd(), "data/DATA/deer.png")), str(group.get("sign", "count", 1)), "🦌币翻倍！" if is_first else "", str(amount), str(coin+amount)))
	else:
		await sign.finish("你今天已经签到过了 ;P")

@profile.handle()
async def _(event: Event):
	data = DataFile(f"[data]/user/{event.user_id}")
	await Putil.reply(profile, event, Message.template("""{}
{}的个人面板
————————————
🦌币：{}
🦌德：{}
""").format(MessageSegment.image(f"https://q1.qlogo.cn/g?b=qq&nk={event.user_id}&s=640"), event.sender.nickname, data.get("profile", "coin", 0), data.get("profile", "lude", 0)))

@rate.handle()
async def _(event: Event, args = RegexGroup()):
	amount = int(args[0])
	data = DataFile(f"[data]/user/{event.user_id}")
	say = ["hso", "社保", "对不良诱惑说Yes", "这一刻，你就是川哥", "kksk"]
	target_data = DataFile(f"[data]/user/{event.reply.sender.user_id}")
	if (event.original_message[0].type == "reply"):
		if (amount > 0):
			if (event.reply.sender.user_id != event.user_id):
				if (data.remove_num("profile", "coin", amount)):
					target_data.add_num("profile", "lude", amount)
					await rate.finish(event.original_message[0] + MessageSegment.at(event.reply.sender.user_id) + Message.template("""
{}！
{}对{}的内容表示了肯定！
————————————
🦌德+{}！！""").format(random.choice(say), event.sender.nickname, event.reply.sender.nickname, str(amount)))
				else:
					await Putil.reply(rate, event, "🦌币不足~")
			else:
				await Putil.reply(rate, event, MessageSegment.at(event.user_id) + " 去得到别人的肯定吧！")
		else:
			await Putil.reply(rate, event, MessageSegment.at(event.user_id) + " ？")
	else:
		await Putil.reply(rate, event, MessageSegment.at(event.user_id) + " 请回复对应消息")

@luclock.handle()
async def _(event: Event):
	data = DataFile(f"[data]/user/{event.user_id}/lu_info")
	dtime = datetime.datetime.now()
	cld = data.get_dataframe("pickle", "calendar", None)
	if (type(cld) == pd.DataFrame):
		last_time = data.get("luclock", "last_time", "无")
		now_delta_time = "无"
		if (last_time != "无"):
			delta_time = dtime - datetime.datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
			now_delta_time = Util.format_delta_time(delta_time)
		total_count = data.get("luclock", "count", 0)
		day_count = 0
		month_count = 0
		month_average = -1
		week_average = -1
		year_average = -1
		max_delta_time = data.get("luclock", "max_delta_time", None)
		max_delta_time = Util.format_delta_time(datetime.timedelta(max_delta_time[0],max_delta_time[1],max_delta_time[2])) if (max_delta_time != None) else "无记录"
		if (dtime.year in cld.index):
			months = cld.at[dtime.year, "months"]
			days = months.loc[dtime.month]
			month_length = calendar.monthrange(dtime.year, dtime.month)[1]

			months_count_df = months.map(lambda x: x.get("count",0) if (type(x) == dict) else 0)
			days_count_df = months_count_df.loc[dtime.month]

			day_count = days.at[dtime.day].get("count", 0)
			month_count = months_count_df.sum().sum()
			month_average = round(month_length/(days_count_df.sum()),2)
			year_average = round((366 if (calendar.isleap(dtime.year)) else 365)/total_count,2)
			if (dtime.day > dtime.weekday()):
				week_count = days_count_df.loc[dtime.day - dtime.weekday():dtime.day].sum()
				week_average = round(7/(week_count), 2) if (week_count > 0 ) else -1
			elif (dtime.month > 1):
				week_count = days_count_df.loc[0:dtime.day].sum() + months_count_df.loc[dtime.month - 1].tail(dtime.weekday() - dtime.day + 1).sum()
				week_average = round(7/(week_count), 2) if (week_count > 0 ) else -1

			#绘图
			match_range(days_count_df,month_length).plot(kind = "bar", x = "day", y ="count", label = "次数", xlabel = "日期", ylabel = "次数", title = "本月统计", figsize = (8, 5))
			plt.xticks(rotation = 0)
			plt.yticks(range(1, max(3, days_count_df.loc[0 : month_length - 1].max() + 1)))
			plt.savefig(data.get_path("month_info.png"))
			match_range(months_count_df.sum(axis = 1),12).plot(kind = "bar", x = "day", y ="count", label = "次数", xlabel = "日期", ylabel = "次数", title = "今年统计", figsize = (8, 5))
			plt.xticks(rotation = 0)
			plt.yticks(range(1, max(3, months_count_df.sum(axis = 1).max() + 1)))
			plt.savefig(data.get_path("year_info.png"))

		mes = f"""{event.sender.nickname} 的🦌钟
——————————
👍累计次数：{total_count}
✨今日次数：{day_count}
🎈本月次数：{month_count}
——————————
⏰上次时间：{last_time}
🎖本周平均：{f"{week_average}天/次" if (week_average != -1) else "无"}
🥉本月平均：{f"{month_average}天/次" if (month_average != -1) else "无"}
🥈今年平均：{f"{year_average}天/次" if (year_average != -1) else "无"}
🥇最大间隔时间：{max_delta_time}
✊现已间隔：{now_delta_time}
——————————"""
		mes += "\n本月次数统计：" + MessageSegment.image(data.get_path("month_info.png"))
		mes += "\n今年次数统计：" + MessageSegment.image(data.get_path("year_info.png"))

		await Putil.reply(luclock, event, mes)
	else:
		await Putil.reply(luclock, event, """未记录~
🦌后@我发送“🦌”或“鹿”来记录🦌的情况吧！""")

@cum.handle()
async def _(event: Event):
	data = DataFile(f"[data]/user/{event.user_id}/lu_info")
	dtime = datetime.datetime.now()
	cld = data.get_dataframe("pickle", "calendar", get_year_calendar(dtime.year))
	if (dtime.year not in cld.index):
		cld = pd.concat([cld, get_year_calendar(dtime.year)])
	last_time = data.get("luclock", "last_time", None)

	month = cld.at[dtime.year, "months"]
	day = month.at[dtime.month, dtime.day]
	count = day.get("count", 0) + 1
	times = day.get("times", [])
	times.append(dtime.strftime("%H:%M:%S"))

	cld.at[dtime.year, "count"] += 1 #年次数
	day["count"] = count
	day["times"] = times
	data.set("luclock", "last_time", dtime.strftime("%Y-%m-%d %H:%M:%S"))
	data.set_dataframe("pickle", "calendar", cld)
	data.set_dataframe("json", "calendar", cld) #仅用于查看
	data.set("luclock", "count", data.get("luclock", "count", 0)+1)
	if (data.get("luclock", "first_time", None) == None):
		data.set("luclock", "first_time", dtime.strftime("%Y-%m-%d %H:%M:%S"))

	if (last_time != None):
		delta_time = dtime - datetime.datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
		last_delta_time = data.get("luclock", "max_delta_time", [0,0,0])
		last_delta_time = datetime.timedelta(days = last_delta_time[0], seconds = last_delta_time[1], microseconds = last_delta_time[2])
		if (delta_time > last_delta_time):
			data.set("luclock", "max_delta_time", [delta_time.days, delta_time.seconds, delta_time.microseconds])
		delta_time = Util.format_delta_time(delta_time)

	await Putil.reply(cum, event, MessageSegment.at(event.user_id) + f""" 哎哟卧槽，你🦌！
💖今天第{count}🦌！
✅已计入🦌钟
""" + (f"""
⏰上次时间：{last_time}
😈间隔时间：{delta_time}""" if (last_time != None) else ""))

@can_lu_today.handle()
async def _(bot: Bot, event: Event):
	lu_chance = random.randint(0, 10000)
	is_lu = random.choices([True, False],[lu_chance, 10000-lu_chance],k=1)[0]
	data = DataFile(f"[data]/user/{event.user_id}/temp_img")
	data.make_dir()
	df = pd.DataFrame({"options": ["鹿", "不鹿"], "chance": [lu_chance, 10000-lu_chance]})
	df.plot(kind = "pie", y = "chance", ylabel = "", radius = 1, fontsize = 24, labels = df.loc[:, "options"], autopct="%1.2f%%", title = "鹿 or not 鹿?", figsize = (6, 6))
	plt.savefig(data.get_path("lu_chance.png"))
	dialogue = [("user", "鹿关大仙，我今日适合🦌吗？"),
	("bot", ["嗯...待吾冥思一番...", "由此时此刻此人此事，吾悟出以下概率"]),
	("bot", MessageSegment.image(data.get_path("lu_chance.png"))),
	("bot", ["待吾算上一番...", f"""结果是：{"鹿" if (is_lu) else "不鹿"}！"""]),
	("user", "谢谢大仙！"),
	("bot", [f"""{"哎哟你操，你🦌！" if (is_lu) else "（汝若真想🦌，吾也没办法）"}""", "评曰："])]
	if (lu_chance <= 1000):
		dialogue.append(("bot", "几率如此之低，真乃天命也！！" if (is_lu) else "如此低的几率，造化弄人"))
	elif (lu_chance <= 4000):
		dialogue.append(("bot", "或天命使然耶？幸甚！" if (is_lu) else "此乃常有之事"))
	elif (lu_chance <= 6000):
		dialogue.append(("bot", "顺理成章耳" if (is_lu) else "天命难违！"))
	elif (lu_chance <= 9000):
		dialogue.append(("bot", "能获得如此大的几率，实乃幸甚至哉" if (is_lu) else "或天使之然也！"))
	elif (abs(10000 - lu_chance) <= 100):
		dialogue.append(("bot", "666这个入是桂"))
	else:
		dialogue.append(("bot", "命中注定！" if (is_lu) else "此乃天意，别无他法"))
	await Putil.send_forward_msg(bot, event, {"user": [event.user_id, event.sender.nickname], "bot": [bot_id, "鹿关大仙"]}, dialogue)

@subscribe_impart.handle()
async def _(event: Event):
	if (isinstance(event, GroupMessageEvent)):
		data = DataFile("[data]/group")
		users = data.get(event.group_id, "impart_users", [])
		if (event.user_id not in users):
			users.append(event.user_id)
			data.set(event.group_id, "impart_users", users)
			await Putil.reply(subscribe_impart, event, "订阅成功~以后这个群有人发音趴都会@你啦")
		else:
			await Putil.reply(subscribe_impart, event, "已经订阅了这个群的音趴了~")
	else:
		await Putil.reply(subscribe_impart, event, "只支持在群聊中使用哦~")

@unsubscribe_impart.handle()
async def _(event: Event):
	if (isinstance(event, GroupMessageEvent)):
		data = DataFile("[data]/group")
		users = data.get(event.group_id, "impart_users", [])
		if (event.user_id in users):
			del users[users.index(event.user_id)]
			data.set(event.group_id, "impart_users", users)
			await Putil.reply(subscribe_impart, event, "取消订阅成功~")
		else:
			await Putil.reply(subscribe_impart, event, "尚未订阅这个群的音趴~")
	else:
		await Putil.reply(subscribe_impart, event, "只支持在群聊中使用哦~")

@impart_receive.handle()
async def _(bot: Bot, event: Event):
	if (event.message[0].type == "json" and isinstance(event, GroupMessageEvent)):
		data = json.loads(event.message[0].data["data"]).get("meta", {}).get("news", {})
		if (data.get("tag", "") == "网易云音乐" and data.get("title", "") == "大家围坐听歌，就等你啦！"):
			data = DataFile("[data]/group")
			users = data.get(event.group_id, "impart_users", [])
			if (len(users) != 0):
				await impart_receive.send(Message([MessageSegment.at(qq) for qq in users]+[MessageSegment.text("\n音趴dd!")]))

@topcoin.handle()
async def _(bot: Bot, event: Event):
	data = DataFile("[data]")
	coins = data.get_multi_files("user", "[read]/profile", {"coin": 0})
	coins = [(x["file"], x["values"]["coin"]) for x in coins]
	coins.sort(key = lambda x: x[1], reverse = True)
	user = ("无", '0')
	for i in range(len(coins)):
		if (coins[i][0] == str(event.user_id)):
			user = (i, coins[i][1])
	s = ["🦌鹿币排行榜Top 10🦌", LINE]
	for i in range(10):
		info = coins[i]
		name = await bot.get_stranger_info(user_id = info[0], no_cached = True)
		s.append(f"第{i+1}名：{name["nickname"]} - {info[1]}")
	s[2] = "🥇" + s[2]
	s[3] = "🥈" + s[3]
	s[4] = "🥉" + s[4]
	s.append(LINE)
	s.append("你当前的排名：")
	s.append(f"第{user[0]+1}名 - {user[1]}")
	await topcoin.finish("\n".join(s))

@present.handle()
async def _(event: Event, args = RegexGroup()):
	user = DataFile(f"[data]/user/{event.user_id}")
	codes = DataFile(f"[data]")
	code = codes.get("gift_code.json", args[0].lower(), None)
	if (code != None):
		dtime = datetime.datetime.now()
		deadline = datetime.datetime.strptime(code.get("deadline"), "%Y-%m-%d %H:%M:%S") if (code.get("deadline") != None) else None
		if (code.get("deadline") == None or dtime < deadline):
			already = code.get("user", [])
			if (event.user_id not in already):
				amount = code.get("amount", 1)
				text = code.get("text", None)
				user.add_num("profile", "coin", amount)
				already.append(event.user_id)
				code["user"] = already
				codes.set("gift_code.json", args[0].lower(), code)
				mes = ["🎉✨兑换成功！✨🎉", f"🦌币 + {amount} ！"]
				if (text != None):
					mes.extend([LINE, text])
				await Putil.reply(present, event, "\n".join(mes))
			else:
				await Putil.reply(present, event, "你已经领取过了！")
		else:
			await Putil.reply(present, event, "兑换码已过期！")
	else:
		await Putil.reply(present, event, "兑换码不存在！")


def get_year_calendar(year):
	month = pd.DataFrame(index = range(1, 13), columns = range(1, 32), dtype = object)
	return pd.DataFrame({
		"months": [month.map(lambda x: {"times": [], "count": 0} if pd.isna(x) else x)],
		"count":[0]}
	,index = [year])

def match_range(df, length, start = 1):
	return pd.DataFrame({"day":pd.Series(range(start,length+1), index = range(start,length+1)), "count":df.loc[start:length - 1]})