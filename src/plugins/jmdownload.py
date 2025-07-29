import jmcomic, os, asyncio

from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot import on_fullmatch, on_message, on_regex
from nonebot.params import RegexGroup
from ..utils.file import DataFile, Logger
from ..utils import util as Util
from ..utils import plugin_util as Putil

jmopt = jmcomic.create_option_by_file(os.path.join(os.getcwd(), "jm_option.yml"))

download = on_regex("^jmcomic (\\d+)$")

@download.handle()
async def _(bot: Bot, event: Event, args = RegexGroup()):
	data = DataFile(f"[data]/user/{event.user_id}", Logger(f"[data]/user/{event.user_id}/log/coin.log", "JM下载"))
	if (data.remove_num("profile", "coin", 10)):
		try:
			fid = await get_folder_id(bot, event.group_id)
			if (await detect_existence(bot, event.group_id, fid, args[0]) == False):
				await Putil.reply(download, event, "下载中...\n（越长时间越久）\n（如果很久还没好就是失败了）")
				info = await get_album(args[0])
				await Putil.reply(download, event, f"【{info.album_id}】{info.name}\n上传中...")
				print("UPLOADING -->", f"{info.album_id}_{info.name}.pdf")
				fpath = os.path.join(os.getcwd(), f"data/JMdownload/pdf/{info.name}.pdf")
				if (await detect_existence(bot, event.group_id, fid, args[0]) == False):
					await bot.upload_group_file(folder = fid, group_id = event.group_id, file = fpath, name = f"{info.album_id}_{info.name}.pdf")
					await Putil.reply(download, event, f"{info.name}\nJM{info.album_id}\n上传完毕\n(还是没有上传？可能是上传时出错了，再试一次)")
				else:
					await Putil.reply(download, event, f"该本子已在本群上传过了！")
			else:
				await Putil.reply(download, event, f"该本子已在本群上传过了！")
			try:
				os.remove(fpath)
				os.remove(os.path.join(os.getcwd(), f"data/JMdownload/{info.name}.zip"))
			except Exception as e:
				pass
		except Exception as e:
			data.add_num("profile", "coin", 10, "退还")
			await Putil.reply(download, event, f"获取失败TT 🦌币已退还\n{e}")
			return
	else:
		await Putil.reply(download, event, "需要10🦌币！")

async def detect_existence(bot, gid, fid, code):
	try:
		content = await bot.get_group_files_by_folder(group_id = gid, folder_id = fid)
		files = [x["file_name"].split("_")[0] for x in content["files"]]
		return code in files
	except Exception:
		return False

async def get_folder_id(bot, gid):
	try:
		await bot.create_group_file_folder(group_id = gid, name = "JM下载", parent_id = "/")
	except Exception as e:
		print(e)
	content = await bot.get_group_root_files(group_id = gid)
	folders = content["folders"]
	for folder in folders:
		if (folder["folder_name"] == "JM下载"):
			print("GET FID -->", folder["folder_id"])
			return folder["folder_id"]
	return "/"

async def get_album(code):
	task = asyncio.create_task(asyncio.to_thread(jmcomic.download_album, code, jmopt))
	content = await task
	return content[0]