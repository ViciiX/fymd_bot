from bs4 import BeautifulSoup as bs
from PIL import Image, ImageFilter
from pydub import AudioSegment
from io import BytesIO
import requests, copy, random, datetime, asyncio, aiohttp, math, json, os

from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot import on_fullmatch, on_message, on_regex
from nonebot.matcher import Matcher
from nonebot.exception import MatcherException, AdapterException
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.params import RegexGroup

from ..utils.file import DataFile, Logger
from ..utils import util as Util
from ..utils import plugin_util as Putil
from ..utils import image_util as ImageUtil

headers = {
    "accept-language": "zh-CN,zh;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Cookie": "PHPSESSID=qr3lo2kohij1g5vvj3osabj3a7; age=verified; existmag=mag"
}
proxy = "http://127.0.0.1:7897"
main_url = "https://www.javbus.com/"

get_music = on_message(priority = 2, block = True)
get_code_info = on_regex("^车牌 (.+)$")
setu = on_regex("^来点色图 (\\d+)$|^来点色图$")
setu_today = on_fullmatch("今日色图")
switch_setu = on_regex("^r18 (开|关)$")

@get_music.handle()
async def _(bot: Bot, event: Event):
	wyy_headers = {
	    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
	    'Accept-Language': 'zh-CN,zh;q=0.9',
	    'Cache-Control': 'no-cache',
	    'Pragma': 'no-cache',
	    'Proxy-Connection': 'keep-alive',
	    'Upgrade-Insecure-Requests': '1',
	    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
	}
	if (event.message[0].type == "json"):
		print(event.message[0].data["data"])
		data = json.loads(event.message[0].data["data"])
		music = data.get("meta",{}).get("music",False)
		#print(music)
		if (music != False):
			await Putil.processing(bot, event)
			await Putil.reply(get_music, event, f"""{music["title"]} - {music["desc"]}
获取中...""")
			music_format = {"网易云": "mp3", "网易云音乐": "mp3", "QQ音乐": "m4a"}
			result = await get_bytes(music["musicUrl"], wyy_headers)
			await Putil.sending(bot, event)
			if (result["status_code"] == 200):
				try:
					await get_music.finish(MessageSegment.record(to_mp3(result["bytes"], music_format[music["tag"]])))
				except AdapterException as e:
					print(e)
					await Putil.reply(get_music, event, "发送超时")
			else:
				await get_music.finish(f"获取失败啦！{result["status_code"]}")

@get_code_info.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	await Putil.ban(get_code_info, event)
	data = DataFile(f"[data]/user/{event.user_id}", Logger(f"[data]/user/{event.user_id}/log/coin.log", "获取车牌号"))
	if (data.remove_num("profile", "coin", 1)):
		await Putil.processing(bot, event)
		try:
			info = await get_info_from_code(args[0])
			if (info["status_code"] == 200):
				try:
					send_str = f"""
片名：{info["name"]}
车牌号：{args[0]}
发行日期：{info.get("date", "暂无")}
时长：{info.get("length", "暂无")}
演员：{"，".join(info.get("actors", ["暂无"]))}
导演：{info.get("director", "暂无")}
制作商：{info.get("producer", "暂无")}
发行商：{info.get("publisher", "暂无")}
分类：{"，".join(info.get("genres", ["暂无"]))}
""".strip()
					await Putil.sending(bot, event)
					# for mes in [MessageSegment.image(info["image"]), send_str, "预览："] + [MessageSegment.image(b) for b in info["samples"]]:
					# 	await get_code_info.send(mes)
					await Putil.send_forward_msg(bot, event, {"bot": [Putil.bot_id, "FyMd"]}, [("bot", [MessageSegment.image(info["image"]), send_str, "预览："] + [MessageSegment.image(b) for b in info["samples"]])])
				except MatcherException:
					pass
				except Exception as e:
					print(type(e),e)
					data.add_num("profile", "coin", 1, log_reason = "发送失败")
					await Putil.reply(get_code_info, event, f"""
发送时发生了一些错误！
{e}
也许是服务器网络波动？待会再试试？
""".strip())

			elif (info["status_code"] == 404):
				data.add_num("profile", "coin", 1, "未找到")
				await Putil.reply(get_code_info, event, "404 Not Fucked")
			else:
				data.add_num("profile", "coin", 1, "获取失败")
				await Putil.reply(get_code_info, event, "发生了一些错误！")
		except asyncio.TimeoutError:
			data.add_num("profile", "coin", 1, log_reason = "获取超时")
			await Putil.reply(get_code_info, event, "获取超时！")
	else:
		await Putil.reply(get_code_info, event, "需要1个🦌币~")

@setu.handle()
async def _(bot: Bot, matcher: Matcher, event: Event, args = RegexGroup()):
	await _setu(bot, matcher, event, False, int(args[0]) if (args[0] != None) else 1)

@setu_today.handle()
async def _(bot: Bot, matcher: Matcher, event: Event):
	await _setu(bot, matcher, event, True)

@switch_setu.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	if (isinstance(event, GroupMessageEvent)):
		members = await bot.get_group_member_list(group_id = event.group_id, no_cached = True)
		members = dict([(member["user_id"], member["role"]) for member in members])
		if (members[event.user_id] in ["owner", "admin"]):
			data = DataFile("[data]/group")
			data.set(event.group_id, "r18_mode", {"开": True, "关": False}[args[0]])
			await Putil.reply(switch_setu, event, f"成功设置r18功能为【{args[0]}】！")
		else:
			await Putil.reply(switch_setu, event, "只有群主或管理员可以开关功能！")
	else:
		await Putil.reply(switch_setu, event, "只能在群聊中使用！")

async def _setu(bot: Bot, matcher: Matcher, event: Event, is_today = False, count = 1):
	await Putil.ban(matcher, event)
	data = DataFile(f"[data]/user/{event.user_id}", Logger(f"[data]/user/{event.user_id}/log/coin.log", "获取色图"))
	count = min(count, 10)
	add_coin = 0
	if (data.remove_num("profile", "coin", count)):
		await Putil.processing(bot, event)
		
		async def get_nodes():
			nodes = []
			async def output(src):
				if (src["status_code"] == 200):
					try:
						nodes.append(MessageSegment.video(src["image"]) if (src["is_video"]) else MessageSegment.image(src["image"]))
						nodes.append(f"""
链接：{src.get("link", "无")}
ID：{src.get("id", "无")}
上传者：{src.get("uploader", "无")}
日期：{src.get("date", "无")}
源链接：{src.get("src", "无")}
评分：{src.get("score", "无")}
最喜爱：{src.get("favorites", "无")}
""".strip())
					except MatcherException:
						pass
					except Exception as e:
						print(e)
						add_coin += 1
						nodes.append(f"发生了一些错误！{e}")
				else:
					add_coin += 1
					nodes.append("哎呀，出错啦~")

			task_list = [get_nsfw_img(is_today) for i in range(count)]
			src_list = [await output(s) for s in await asyncio.gather(*task_list)]
			return nodes

		nodes = await get_nodes()
		await Putil.sending(bot, event)
		try:
			if (isinstance(event, GroupMessageEvent)):
				await Putil.send_forward_msg(bot, event, {"bot": [Putil.bot_id, "FyMd"]}, [("bot",nodes)])
			else:
				for mes in nodes:
					await matcher.send(mes)
		except AdapterException as e:
			print(e)
			add_coin = count
			await Putil.reply(matcher, event, "发送失败TT，🦌币已返还")
		data.add_num("profile", "coin", add_coin, log_reason = "发送失败退还")

	else:
		await Putil.reply(matcher, event, f"需要{count}个🦌币~")

async def get_info_from_code(code):
	async with aiohttp.ClientSession() as session:
		async with session.get(headers = headers, url = main_url + code, timeout = 20, proxy = proxy) as response:
			if (response.status == 200):
				soup = bs(await response.text(), 'lxml')
				info = [list(x.stripped_strings) for x in soup.find("div", class_ = "col-md-3 info").find_all("p")]
				result = {
					'status_code': 200,
					'name': soup.find("title").get_text().replace(" - JavBus", "")
				}
				img_url = "https://www.javbus.com" + soup.find("div", class_ = "col-md-9 screencap").find("img").get("src")
				img_header = copy.deepcopy(headers)
				img_header["Referer"] = main_url + code
				img_result = await get_img(img_url, img_header)
				result["image"] = img_result["img"]
				for i in range(0, len(info)):
					p = info[i]
					if (p[0] == "發行日期:"):
						result["date"] = p[1]
					elif (p[0] == "長度:"):
						result["length"] = p[1]
					elif (p[0] == "製作商::"):
						result["producer"] = p[1]
					elif (p[0] == "發行商::"):
						result["publisher"] = p[1]
					elif (p[0] == "導演:"):
						result["director"] = p[1]
					elif (p[0] == "類別:"):
						if (i+1 < len(info)):
							result["genres"] = info[i + 1]
					elif (p[0] == "演員"):
						if (i+1 < len(info)):
							result["actors"] = info[i + 1]
				#预览图
				cont = soup.find("div", class_="container").find("div", id="sample-waterfall")
				sample_urls = [x.get("href") for x in cont.find_all("a")]
				print(sample_urls)
				sample_bytes = [get_img(u, img_header) for u in sample_urls]
				result["samples"] = [r["img"] for r in await asyncio.gather(*sample_bytes)]
				return result
			else:
				return {'status_code': response.status}

async def get_nsfw_img(is_today = False):
	url = f"https://danbooru.donmai.us/explore/posts/popular?page={random.randint(1,50)}"
	if (is_today == False):
		dtime = datetime.datetime.now()
		year = random.randint(dtime.year - 3, dtime.year)
		month = random.randint(1,12) if (year < dtime.year) else random.randint(1, dtime.month)
		day = random.randint(1, 28) if (year < dtime.year or (year == dtime.year and month < dtime.month)) else random.randint(1, dtime.day-1)
		url = f"https://danbooru.donmai.us/explore/posts/popular?date={year}-{month}-{day}&page={random.randint(1, 10) if (is_today) else random.randint(1, 5)}&scale=day"
	async with aiohttp.ClientSession() as session:
		async with session.get(url = url, timeout = 20, proxy = proxy) as response:
			result = {
				"status_code": response.status,
				"is_video": False
			}
			if (response.status == 200):
				soup = bs(await response.text(), 'lxml')
				print(url)
				articles = soup.find("div", class_ = "posts-container gap-2")
				if (articles == None):
					print("reload image")
					result = get_nsfw_img()
				else:
					index = random.randint(0, 19) if (is_today) else random.randint(0, 4)
					print(f"choose: {index}")
					src = [[x.get("data-id"), x.find("img").get("src")] for x in articles.find_all("article", limit=(20 if (is_today) else 5))][index]
					result["link"] = f"https://danbooru.donmai.us/posts/{src[0]}"
					async with aiohttp.ClientSession() as session:
						async with session.get(url = result["link"], timeout = 20, proxy = proxy) as response:
							result["status_code"] = response.status
							if (response.status == 200):
								soup = bs(await response.text(), 'lxml')
								print(f"post link:{result["link"]}")
								src = soup.find("div", class_ = "sidebar-container flex sm:flex-col gap-3").find("img", class_ = "fit-width")
								if (src == None):
									result["is_video"] = True
									src = soup.find("div", class_ = "sidebar-container flex sm:flex-col gap-3").find("video", class_ = "fit-width")
								src = src.get("src")
								infos = soup.find_all("section", id = "post-information")[0]
								infos = [[i for i in x.stripped_strings] for x in infos.find("ul").children if x != "\n"]
								for info in infos:
									if (info[0].startswith("ID")):
										result["id"] = info[0].split(": ")[1]
									elif (info[0] == "Uploader:"):
										result["uploader"] = info[1] if (len(info) > 1) else None
									elif (info[0] == "Date:"):
										result["date"] = info[1] if (len(info) > 1) else None
									elif (info[0] == "Source:"):
										result["src"] = info[1] if (len(info) > 1) else None
									elif (info[0] == "Score:"):
										result["score"] = info[1] if (len(info) > 1) else None
									elif (info[0] == "Favorites:"):
										result["favorites"] = info[1] if (len(info) > 1) else None
								img_result = await get_img(src, None, result["is_video"] == False)
								result["image"] = img_result["img"]
			return result

async def get_img(url, headers = None, is_proc = True, timeout = 20, proxy = proxy):
	result = await get_bytes(url, headers, timeout, proxy)
	if (is_proc):
		result["bytes"] = ImageUtil.img_process(result["bytes"]).getvalue()
	result["img"] = result.pop("bytes")

	#for test
	# with open(f"test/{url.split("/")[-1]}.png", "wb") as f:
	# 	f.write(result["img"])

	return result

async def get_bytes(url, headers = None, timeout = 20, proxy = proxy):
	print("get_bytes_url:", url)
	result = {
		"status_code": 0,
		"bytes": None
	}
	try:
		async with aiohttp.ClientSession() as session:
			async with session.get(url = url, headers = headers, timeout = 20, proxy = proxy) as response:
				result["status_code"] = response.status
				if (response.status == 200):
					result["bytes"] = await response.content.read()
	except Exception as e:
		print(f"get_bytes_err: {e}")
		result["status_code"] = -1
	print("get_bytes_result:", result["status_code"], BytesIO(result["bytes"]))
	return result

def to_mp3(file_bytes, raw_format):
	audio = AudioSegment.from_file(BytesIO(file_bytes), format = raw_format)
	bytes_io = BytesIO()
	audio.export(bytes_io, "mp3")
	return bytes_io.getvalue()