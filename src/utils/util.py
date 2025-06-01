import math, random, os, math, zipfile
from PIL import Image, ImageFilter
from io import BytesIO
from nonebot.adapters.onebot.v11 import Message

def make_line(mes, char = "─"):
	return char*15 + "\n" + mes + "\n" + char*15

def make_line_auto(mes, char = "─"):
	string = ""
	if type(mes) == Message:
		string = mes.extract_plain_text()
	else:
		string = mes
	LIMIT = 15
	count = 0
	halflist = r"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:<>?{}|!@#$%^&*()_+~,./;'[]-="
	for i in search_longest(string.split("\n")):
		if i in halflist:
			count += 0.5
		else:
			count += 1
	count = min(math.ceil(count), LIMIT)
	return char*count + "\n" + mes + "\n" + char*count

def search_longest(arr):
	result = ""
	for i in arr:
		if len(i) > len(result):
			result = i
	return result

def random_int(arr):
	return random.randint(arr[0], arr[1])

def get_all_file(path, file_name, force_mode = False):
	result = []
	for name in os.listdir(path):
		next_path = os.path.join(path,name)
		if os.path.isdir(next_path):
			result.extend(get_all_file(next_path, file_name))
		elif name.split(".")[0] == file_name and force_mode == False:
			result.append(os.path.join(path,name))
		elif name == file_name and force_mode == True:
			result.append(os.path.join(path,name))
	return result

def format_delta_time(delta_time):
	year = delta_time.days//365
	day = delta_time.days%365
	hour = delta_time.seconds//3600
	minute = (delta_time.seconds//60)%60
	second = delta_time.seconds%60
	return f"""{f"{year}年" if (year > 0) else ""}{f"{day}天" if (day > 0) else ""}{f"{hour}小时" if (hour > 0) else ""}{f"{minute}分" if (minute > 0) else ""}{f"{second}秒" if (second > 0) else ""}"""

def get_dir_size(dir):
	size = 0
	for root, dirs, files in os.walk(dir):
		size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
	return size

def format_file_size(size_bytes):
	if size_bytes == 0:
		return "0 B"
	size_name = ("B", "KB", "MB", "GB", "TB")
	i = int(math.floor(math.log(size_bytes, 1024)))
	p = math.pow(1024, i)
	s = round(size_bytes / p, 2)
	return f"{s} {size_name[i]}"

def zip_dir(dirpath, outFullName, exclude_dirs = []):
	"""
	压缩指定文件夹
	:param dirpath: 目标文件夹路径
	:param outFullName: 压缩文件保存路径+xxxx.zip
	:return: 无
	"""
	zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
	for path, dirnames, filenames in os.walk(dirpath):
		# 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
		dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
		fpath = path.replace(dirpath, '')

		for filename in filenames:
			zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
	zip.close()

def img_process(img_bytes):
	try:
		img = Image.open(BytesIO(img_bytes))
		img = img.convert("RGBA").crop((0, 0, img.size[0]+random.randint(-10, 10), img.size[1]+random.randint(-10, 10))).filter(ImageFilter.UnsharpMask(random.randint(1,5)/10, random.randint(50, 150)))
		return img_to_bytesio(img, "PNG")
	except Exception as e:
		print(e)
		return img_bytes

def thumbnail(img, size):
	img = Image.open(img)
	img.thumbnail(size)
	return img_to_bytesio(img, img.format if (img.format != None) else "PNG")

def img_to_bytesio(img, img_format):
	i = BytesIO()
	img.save(i, format = img_format)
	return i