import pandas as pd
import os, json, datetime, random
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageColor

from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot import on_fullmatch, on_message, on_regex
from nonebot.params import RegexGroup

from ..utils.file import DataFile
from ..utils import util as Util
from ..utils import plugin_util as Putil

wordle_path = "data/DATA/wordle"
endict = pd.read_pickle(os.path.join(os.getcwd(), wordle_path, "endict.pkl"))
font_path = os.path.join(os.getcwd(), wordle_path, "wordle_font.ttf")

check = on_fullmatch("wordle")
create = on_regex("^wordle (\\d+|/)$|^wordle (\\d+|/) (zk|gk|cet4|cet6|toefl|gre)$")
ans = on_regex("^wd (.+)$")
show_ans = on_fullmatch("wordle answer")


@check.handle()
async def _(event: Event):
	wd = DataFile(f"[data]/wordle/{event.group_id if isinstance(event, GroupMessageEvent) else event.user_id}")
	words = wd.get("info", "word", [])
	answer = wd.get("info", "answer", "")
	tag = wd.get("info", "tag", None)
	if (words != []):
		await check.send(MessageSegment.image(get_wordle_img(words, answer)))
		await check.finish(f"""单词长度：{len(answer)}
创建时间：{wd.get("info", "date", "无")}
标签：{tag if (tag != None) else "任意"}
{"进行中" if (wd.get("info", "is_finished", True) == False) else "已结束"}""")
	else:
		await Putil.reply(check, event, "当前对话没有进行中的wordle！")

@create.handle()
async def _(event: Event, args = RegexGroup()):
	wd = DataFile(f"[data]/wordle/{event.group_id if isinstance(event, GroupMessageEvent) else event.user_id}")
	length = args[0] if (args[0] != None) else args[1]
	if (length == "/"):
		word = endict.loc[:, "word"]
	else:
		length = int(length)
		if (4 <= length and length <= 15):
			word = get_target_word(length, args[2])
		else:
			await Putil.reply(create, event, "只支持4~15长度的单词~")
			return
	if (word.empty == False):
		word = word.sample().values[0]
		info = json.loads(endict.loc[endict.loc[:, "word"] == word].reset_index().to_json())
		wd.set_by_dict("info", {"word": [], "answer": word, "info": info, "is_finished": False, "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "tag": args[2]})
		await create.send(MessageSegment.image(get_wordle_img([], word)))
		await create.finish(f"""新的wordle已创建！
单词长度：{len(word)}
标签：{args[2] if (args[2] != None) else "任意"}""")
	else:
		await Putil.reply(create, event, "没找到单词~")

@ans.handle()
async def _(event: Event, args = RegexGroup()):
	word = args[0].lower()
	if (endict.loc[endict.loc[:, "word"] == args[0]].empty == False or endict.loc[endict.loc[:, "word"] == word].empty == False):
		wd = DataFile(f"[data]/wordle/{event.group_id if isinstance(event, GroupMessageEvent) else event.user_id}")
		words = wd.get("info", "word", [])
		answer = wd.get("info", "answer", "")
		if (len(word) == len(answer)):
			if (wd.get("info", "is_finished", False) == False):
				is_finished = False
				if (args[0] == answer or word == answer):
					is_finished = True
					user = DataFile(f"[data]/user/{event.user_id}")
					prize = random.randint(10, 20)
					user.add_num("profile", "coin", prize)
					await Putil.reply(ans, event, f"恭喜你猜对了！奖励你{prize}🦌币！")
				elif (word != answer and len(words) == 5):
					is_finished = True
				words.append(word)
				wd.set("info", "word", words)
				wd.set("info", "is_finished", is_finished)
				await ans.send(MessageSegment.image(get_wordle_img(words, answer)))
				if (is_finished):
					info = wd.get("info", "info", {})
					await ans.finish(f"""单词：{answer}
音标：[{info.get("phonetic", {}).get("0", "未找到")}]
中文释义：
{info.get("translation", {}).get("0", "未找到").replace("\\n", "\n")}
词频排名：{info.get("frq", {}).get("0", "未找到")}""")
			else:
				await Putil.reply(ans, event, "这一轮wordle已经结束了~开启新一轮吧~")
		else:
			await Putil.reply(ans, event, "长度不一样哦~")
	else:
		await Putil.reply(ans, event, "不是有效的英语单词~试试用原型？")

@show_ans.handle()
async def _(event: Event):
	wd = DataFile(f"[data]/wordle/{event.group_id if isinstance(event, GroupMessageEvent) else event.user_id}")
	words = wd.get("info", "word", [])
	answer = wd.get("info", "answer", "")
	info = wd.get("info", "info", {})
	wd.set("info", "is_finished", True)
	await show_ans.send(MessageSegment.image(get_wordle_img(words, answer)))
	await show_ans.finish(f"""单词：{answer}
音标：[{info.get("phonetic", {}).get("0", "未找到")}]
中文释义：
{info.get("translation", {}).get("0", "未找到").replace("\\n", "\n")}
词频排名：{info.get("frq", {}).get("0", "未找到")}""")

def get_target_word(word_length = None, tag = None):
	word = endict.loc[:,"word"]
	target_words = word
	if (word_length != None):
		length_mask = word.map(lambda x: len(x) == word_length)
		target_words = word.loc[length_mask]
	if (tag != None):
		tags = endict.loc[:,"tag"].loc[length_mask] if (word_length != None) else endict.loc[:,"tag"]
		tag_mask = tags.map(lambda x: bool(set([tag] if (type(tag) == str) else tag) & set(x.split(" "))) if (type(x) == str) else False)
		target_words = target_words.loc[tag_mask]
	return target_words.reset_index().loc[:, "word"]

def create_pane(letter, mode, img_size = 128):
	if (mode == "normal"):
		bg_color = "#FFFFFF"
		font_color = "#000000"
		border_color = "#787C7E"
	elif (mode == "correct"):
		bg_color = "#6AAA64"
		font_color = "#FFFFFF"
		border_color = bg_color
	elif (mode == "nearly"):
		bg_color = "#C9B458"
		font_color = "#FFFFFF"
		border_color = bg_color
	elif (mode == "incorrect"):
		bg_color = "#787C7E"
		font_color = "#FFFFFF"
		border_color = bg_color
	elif (mode == "empty"):
		bg_color = "#FFFFFF"
		font_color = "#FFFFFF"
		border_color = "#D3D6DA"
	img = Image.new("RGBA", (img_size, img_size), color = bg_color)
	font = ImageFont.truetype(font = font_path, size = 100 * (128//img_size))
	draw = ImageDraw.Draw(img)
	draw.rectangle(xy = [(0, 0), (img_size, img_size)], width = 5 * (128//img_size), outline = border_color)
	draw.text(xy = (img_size//2, img_size//2), text = letter, fill = font_color, font = font, anchor = "mm")
	return img

def get_word_img(word, answer, img_size = 128, horizontal_margin = 64, vertical_margin = 64, gap = 32):
	word = word.upper()
	answer = answer.upper()
	img = Image.new("RGBA", (img_size * len(word) + gap * (len(word) - 1) + horizontal_margin * 2, img_size + vertical_margin * 2), color = "#FFFFFF")
	for i in range(len(word)):
		char = word[i]
		if (word[i] == answer[i]):
			mode = "correct"
		elif (word[i] in answer):
			mode = "nearly"
		elif (word[i] == " "):
			mode = "empty"
		else:
			mode = "incorrect"
		img.paste(create_pane(char, mode), (horizontal_margin + (img_size + gap) * i, vertical_margin))
	return img

def get_wordle_img(words, answer, img_size = 128, horizontal_margin = 64, vertical_margin = 64, horizontal_gap = 32, vertical_gap = 32):
	words = [x.upper() for x in words]
	words += [" " * len(answer)] * (6 - len(words))
	answer = answer.upper()
	img = Image.new("RGBA", (img_size * len(answer) + horizontal_gap * (len(answer) - 1) + horizontal_margin * 2, img_size * len(words) + vertical_gap * (len(words) - 1) + vertical_margin * 2), color = "#FFFFFF")
	for i in range(len(words)):
		word = words[i]
		paste_img = get_word_img(word, answer, img_size, 0, 0, horizontal_gap)
		img.paste(paste_img, (horizontal_margin, vertical_margin  + (img_size + vertical_gap) * i))
	b = BytesIO()
	img.save(b, "PNG")
	return b