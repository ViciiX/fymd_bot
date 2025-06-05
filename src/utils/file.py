import os, json, re
import pandas as pd

class DataFile:
	def __init__(self, path = "[data]"):
		self.error = ""
		self.path = path.replace("[data]", os.path.join(os.getcwd(),"data")).replace("[main]", os.getcwd())

	def set_path(self, path):
		self.path = path.replace("[data]", os.path.join(os.getcwd(),"data")).replace("[main]", os.getcwd())

	def get_path(self, path):
		return os.path.join(self.path, str(path))

	def make_dir(self, path = ""):
		path = os.path.join(self.path, path)
		if (not os.path.exists(os.path.dirname(path))):
			os.makedirs(os.path.dirname(path))

	def get(self, path, key, value = ""):
		path = os.path.join(self.path, str(path))
		try:
			with open(path,"r", encoding='utf-8') as file:
				try:
					data = json.loads(file.read())
					self.error = ""
					return data[key] if (key != None) else data
				except Exception as err:
					self.error = err
					return value
		except Exception as e:
			self.error = e
			#print(e)
			return value

	def get_raw(self, path):
		path = os.path.join(self.path, path)
		try:
			with open(path,"r", encoding='utf-8') as file:
				try:
					self.error = ""
					return json.loads(file.read())
				except Exception as err:
					print(err)
					self.error = err
					return False
		except Exception as e:
			self.error = e
			print(e)
			return False

	def set_text(self, path, text):
		path = os.path.join(self.path, str(path))
		try:
			if (not os.path.exists(os.path.dirname(path))):
				os.makedirs(os.path.dirname(path))
			with open(path,"w", encoding='utf-8') as file:
				file.write(text)
			self.error = ""
			return ""
		except Exception as e:
			self.error = e
			print(e)
			return e

	def set(self, path, key, value):
		path = os.path.join(self.path, str(path))
		try:
			if (not os.path.exists(os.path.dirname(path))):
				os.makedirs(os.path.dirname(path))
			data = {}
			try:
				with open(path,"r", encoding='utf-8') as f:
					data = json.loads(f.read())
			except Exception:
				pass
			data[key] = value
			with open(path,"w", encoding='utf-8') as file:
				file.write(json.dumps(data, ensure_ascii = False, indent = "\t"))
			self.error = ""
			return ""
		except Exception as e:
			self.error = e
			print(e)
			return e


	def add_num(self, path, key, value):
		current_value = self.get(path, key, 0)
		if (type(current_value) == int):
			self.set(path, key, current_value + value)
			return current_value + value
		else:
			return "str"

	def remove_num(self, path, key, value):
		current_value = self.get(path, key, 0)
		if (type(current_value) == int):
			if (current_value >= value):
				self.set(path, key, current_value - value)
				return True
			else:
				return False
		else:
			return "str"

	def get_by_list(self, path, keys, values):
		result = {}
		for i in range(len(keys)):
			value = values
			if (type(values) == list):
				value = values[i]
			result[keys[i]] = self.get(path, keys[i], value)
		return result

	def get_in_list(self, path, keys, values):
		result = []
		for i in range(len(keys)):
			value = values
			if (type(values) == list):
				value = values[i]
			result.append(self.get(path, keys[i], value))
		return result

	def get_by_dict(self, path, dic):
		for key in dic.keys():
			dic[key] = self.get(path, key, dic[key])
		return dic

	def set_by_list(self, path, keys, values):
		result = {}
		for i in range(len(keys)):
			value = values
			if (type(values) == list):
				value = values[i]
			if (self.set(path, keys[i], value) != ""):
				return self.error
		return ""

	def set_by_dict(self, path, dic):
		for key in dic.keys():
			if (self.set(path, key, dic[key]) != ""):
				return self.error
		return ""

	def get_loop(self, path, raw_keys, default_value):
		path = os.path.join(self.path, path)
		keys = raw_keys.split(".") if (type(raw_keys) == str) else raw_keys
		obj = self.get(path, None, {})
		for key in keys:
			obj = obj.get(key, None)
			if (obj == None):
				return default_value
		return obj

	def get_loop_by_dict(self, path, dic):
		result_dic = {}
		for key in dic.keys():
			result_dic[key] = self.get_loop(path, key, dic[key])
		return result_dic

	def get_dataframe(self, mode, path, default_value, add_ext = True):
		path = os.path.join(self.path, str(path))
		ext = {"csv": "csv", "json":"json", "html":"html", "excel":"xlsx", "pickle": "pkl"}
		try:
			if (mode in list(ext.keys())):
				return getattr(pd, f"read_{mode}")(f"{path}{f".{ext[mode]}" if (add_ext) else ""}")
		except Exception as e:
			self.error = e
			print(e)
			return default_value

	def set_dataframe(self, mode, path, dataframe, add_ext = True):
		path = os.path.join(self.path, str(path))
		ext = {"csv": "csv", "json":"json", "html":"html", "excel":"xlsx", "pickle": "pkl"}
		try:
			if (mode in list(ext.keys())):
				return getattr(dataframe, f"to_{mode}")(f"{path}{f".{ext[mode]}" if (add_ext) else ""}")
		except Exception as e:
			self.error = e
			print(e)
			return False

	def remove(self, path, key):
		path = os.path.join(self.path, str(path))
		try:
			if (not os.path.exists(os.path.dirname(path))):
				os.makedirs(os.path.dirname(path))
			data = {}
			with open(path,"r", encoding='utf-8') as f:
				data = json.loads(f.read())
			result = data.pop(key)
			with open(path,"w", encoding='utf-8') as file:
				file.write(json.dumps(data, ensure_ascii = False, indent = "\t"))
			self.error = ""
			return result
		except Exception as e:
			self.error = e
			print(e)
			return 

	def get_files(self, path, add_path = False, contain_dir = False, contain_file = True):
		path = os.path.join(self.path, str(path))
		try:
			return [(os.path.join(path, f) if add_path else f) for f in os.listdir(path) if ( (os.path.isfile(os.path.join(path, f)) and contain_file) or (os.path.isfile(os.path.join(path, f)) == False and contain_dir) )]
		except Exception as e:
			print(e)
			return []

	def delete(self, path):
		path = os.path.join(self.path, str(path))
		try:
			os.remove(path)
			return True
		except Exception as e:
			print(e)
			return False

	def get_multi_files(self, dir_path, file_path, key_and_value):
		path = os.path.join(self.path, dir_path)
		files = []
		result = []
		if ("/" in file_path):
			files = self.get_files(path, False, True, False)
		else:
			files = self.get_files(path, False)
		for file_name in files:
			data = DataFile(os.path.join(path, os.path.dirname(file_path).replace("[read]", file_name)))
			result.append({"file": file_name, "values": data.get_loop_by_dict(os.path.basename(file_path), key_and_value)})
		return result

class Item:
	def __init__(self, path = "[data]"):
		self.error = ""
		self.path = os.path.dirname(path)
		self.file = os.path.basename(path)
		self.data = DataFile(self.path)
		self.items = self.data.get(self.file, "items", [])

	def save(self):
		self.data.set(self.file, "items", self.items)

	def find(self, tname, tdata = None):
		return Item.value_find(self.items, tname, tdata)

	def in_range(self, tname, num_range, tdata = None):
		item = self.find(tname, tdata)[1]
		return num_range[0] <= item["amount"] and item["amount"] < num_range[1] 

	def add(self, tname, amount, tdata = None, is_save = True):
		self.items = Item.value_add(self.items, tname, amount, tdata)
		if (is_save):
			self.save()

	def add_by_list(self, item_list, is_save = True):
		add_items = []
		for item in item_list:
			add_items = Item.value_add(add_items, item["name"], item["amount"], item.get("data", None))
		for i in add_items:
			self.add(i["name"], i["amount"], i.get("data", None), is_save)

	def remove(self, tname, amount, tdata = None):
		item = self.find(tname, tdata)
		if (item[0] == -1):
			return False
		else:
			if (self.items[item[0]]["amount"] >= amount):
				self.items[item[0]]["amount"] -= amount
				return True
			else:
				return False
		self.save()

	def format_items(template, limit = -1, callables = {}):
		return Item.format(self.items, template, limit)

	@staticmethod
	def value_find(values, name, data = None):
		for i in range(len(values)):
			tname = values[i]["name"]
			tdata = values[i]["data"]
			if (name == tname and (data == tdata or data == None)):
				return (i, values[i])
		return (-1, None)

	@staticmethod
	def value_add(origin_values, name, amount, data = None):
		item = Item.value_find(origin_values, name, data)
		if (item[0] == -1):
			origin_values.append({"name": name, "amount": amount, "data": data if (data != None) else {}})
		else:
			origin_values[item[0]]["amount"] += amount
		return origin_values

	@staticmethod
	def format(items, template, limit = -1, callables = {}):
		s = []
		pattern = r"(\[.*?\])"
		template = re.split(pattern, template)
		template = [x for x in template if (x != "")]
		for i in range(len(items)):
			if (i == limit):
				break
			item = items[i]
			t = template.copy()
			for j in range(len(t)):
				if (t[j] == "[index]"):
					t[j] = i + 1
				elif (t[j] == "[name]"):
					t[j] = item["name"]
				elif (t[j] == "[amount]"):
					t[j] = item["amount"]
				elif (t[j].startswith("[data")):
					t[j] = item["data"][t[j][1 : len(t[j])-1].split(":")[1]]
				elif (t[j].startswith("[call")):
					#key: k
					k = t[j][1 : len(t[j])-1].split(":")[1]
					t[j] = callables[k][0](item, **callables[k][1])
			s.append("".join([str(x) for x in t]))

		return "\n".join(s)