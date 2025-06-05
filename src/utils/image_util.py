import qrcode, random
from PIL import Image, ImageFilter
from io import BytesIO

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