from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot import on_fullmatch, on_message, on_regex
from nonebot.rule import to_me
from nonebot.params import RegexGroup

from ..utils.file import DataFile
from ..utils import util as Util
from ..utils import plugin_util as Putil
from ..utils import image_util as ImageUtil

forhelp = on_regex("^(.*帮助)( (\\d)+)?$")

@forhelp.handle()
async def _(event: Event, args = RegexGroup()):
	data = DataFile("[data]/DATA")
	if (data.get("help.json", args[0], None) != None):
		if (args[2] == None):
			help_dict = data.get("help.json", args[0], {})
			text = f"""功能列表
————————————
{"\n".join([f"{i}.{list(help_dict.keys())[i]}" for i in range(len(help_dict.keys()))])}
————————————
发送“{args[0]} [序号]”获取详细帮助
如：{args[0]} 0
————————————"""
			mes = Message.template("""{}
对于某些功能：
回应{}时表示正在获取/处理
回应{}时表示正在发送信息
""").format(MessageSegment.image(ImageUtil.text_to_image(text, width = None, margin = 50, qq = event.user_id)), MessageSegment.face(424), MessageSegment.face(124))
			await Putil.reply(forhelp, event, mes)
		else:
			data = DataFile("[data]/DATA")
			help_dict = data.get("help.json", args[0], {})
			help_list = list(help_dict.keys())
			index = int(args[2])
			if (0 <= index and index <= len(help_list)-1):
				mes = [help_list[index], "————————————", "\n".join(help_dict[help_list[index]])]
				await Putil.reply(forhelp, event, MessageSegment.image(ImageUtil.text_to_image(mes, width = None, margin = 50, qq = event.user_id)))
			else:
				await Putil.reply(forhelp, event, "404 Not Fucked")