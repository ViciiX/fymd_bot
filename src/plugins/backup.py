import zipfile, datetime, os

from nonebot import require, on_fullmatch
from ..utils.file import DataFile
from ..utils import util as Util
from nonebot.permission import SUPERUSER

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

MAX = 20
DELTA = 60 * 30

b = on_fullmatch("#backup", permission = SUPERUSER)

@b.handle()
async def _():
	backup()
	await b.finish("BACKUP COMPLETED")

def backup():
	data = DataFile("[data]/backup")
	history = data.get("history.json", "history", [])
	if (len(history) > MAX - 1):
		print(f"REMOVED {history[0]}")
		data.delete(history[0])
		del history[0]
	file_path = datetime.datetime.now().strftime("%Y-%m-%d_%H时%M分%S秒.zip")
	history.append(file_path)
	file_path = os.path.join(DataFile("[data]/BACKUP").path, file_path)
	Util.zip_dir(DataFile("[data]").path, file_path, ["DATA", "BACKUP"])
	data.set("history.json", "history", history)
	print("BACKUP COMPLETED")

backup()

scheduler.add_job(backup, "interval", seconds = DELTA)