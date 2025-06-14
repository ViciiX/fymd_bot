import qrcode, random, math
from PIL import Image, ImageFilter, ImageFont, ImageDraw
from io import BytesIO
from pilmoji import Pilmoji

from .file import DataFile

def img_process(img_bytes):
	try:
		img = Image.open(BytesIO(img_bytes))
		img = img.convert("RGBA").crop((0, 0, img.size[0]+random.randint(-10, 10), img.size[1]+random.randint(-10, 10))).filter(ImageFilter.UnsharpMask(random.randint(1,5)/10, random.randint(50, 150)))
		return img_to_bytesio(img, "PNG")
	except Exception as e:
		print(e)
		return img_bytes

def thumbnail(img, size):
	img = Image.open(img) if (type(img) == str) else img
	img.thumbnail(size)
	return img_to_bytesio(img, img.format if (img.format != None) else "PNG")

def img_to_bytesio(img, img_format = "PNG"):
	i = BytesIO()
	img.save(i, format = img_format)
	return i

def get_qr(text, fill_color = "black", back_color = "white"):
	qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
	qr.add_data(text)
	qr.make(fit=True)
	return qr.make_image(fill_color = fill_color, back_color = back_color)

def text_to_image(raw_texts, width = "square", bg_color = "white", font_name = "Noto", font_size = 32, font_color = "black", margin = 100, min_size = (256, 256), in_bytes = True, qq = None):
	
	#自定义字体、背景配置
	if (qq != None):
		user_data = DataFile(f"[data]/user/{qq}").get("settings.json", "text_to_image", {})
		bg_color = user_data.get("bg_color", bg_color)
		font_name = user_data.get("font_name", font_name)
		font_color = user_data.get("font_color", font_color)

	texts = []
	d = DataFile("[data]/DATA/font")
	raw_texts = [raw_texts] if (type(raw_texts) == str) else raw_texts
	for text in raw_texts:
		texts.extend(text.split("\n"))
	texts = [x if (x != "") else "\n" for x in texts]
	font = ImageFont.truetype(d.get_path(f"{font_name}.ttf"), size = font_size)
	
	if (width == None):
		width = max([font.getbbox(text)[2] for text in texts])
	else:
		if (width == "square"):
			box = font.getbbox("\n".join(texts))
			width = round(math.sqrt(box[2] * box[3]))
		elif (type(width) == list):
			box = font.getbbox("\n".join(texts))
			width = round(math.sqrt(box[2] * box[3] * width[0] / width[1]))
		new_texts = []
		for text in texts:
			s = ""
			for char in text:
				if (font.getbbox(s + char)[2] > width):
					new_texts.append(s)
					s = ""
				s += char
			if (s != ""):
				new_texts.append(s)
		texts = new_texts

	width = max(min_size[0], width + margin * 2)
	height = max(min_size[1], margin * 2 + round(font.getbbox("汉字")[3] * 1.5) * len(texts))
	
	with Image.new(mode = "RGBA", size = (width, height), color = bg_color) as img:
		try:
			with Pilmoji(img) as draw:
				draw.text(xy = (margin, margin), text = "\n".join(texts), fill = font_color, font = font, emoji_scale_factor = 0.9)
		except Exception:
			draw = ImageDraw.Draw(img)
			draw.text(xy = (margin, margin), text = "\n".join(texts), fill = font_color, font = font)
		return img_to_bytesio(img) if (in_bytes) else img

def get_color_avaliable(color):
	try:
		Image.new(mode = "RGBA", size = (1,1), color = color)
		return True
	except Exception as e:
		return False
