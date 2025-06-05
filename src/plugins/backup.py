import zipfile, datetime, os

from nonebot import require, on_fullmatch
from ..utils.file import DataFile
from ..utils import util as Util
from nonebot.permission import SUPERUSER

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

MAX = 1024 #MB
DELTA = 60 * 30
max_size = 0

b = on_fullmatch("#backup", permission = SUPERUSER)

@b.handle()
async def _():
	backup()
	await b.finish("BACKUP COMPLETED")

def backup():
	global max_size
	data = DataFile("[data]/BACKUP")
	history = data.get("history.json", "history", [])
	if (len(history) > max_size - 1):
		print(f"REMOVED {history[0]}")
		data.delete(history[0])
		del history[0]
	file_path = datetime.datetime.now().strftime("%Y-%m-%d_%H时%M分%S秒.zip")
	history.append(file_path)
	file_path = os.path.join(data.path, file_path)
	Util.zip_dir(DataFile("[data]").path, file_path, ["DATA", "BACKUP"])
	file_size = os.path.getsize(file_path)
	max_size = (MAX ** 3)/file_size
	data.set("history.json", "history", history)
	print("BACKUP COMPLETED")

file_path = [x for x in os.listdir(DataFile("[data]/BACKUP").path) if x.endswith(".zip")]
file_size = os.path.getsize(os.path.join(DataFile("[data]/BACKUP").path, file_path[0]))
max_size = (MAX ** 3)/file_size
print(f"RUN IN MAX_SIZE --> {max_size}")
backup()

scheduler.add_job(backup, "interval", seconds = DELTA)