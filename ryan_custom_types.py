import collections
import json
import os

class AutoUpdatingJSON(collections.UserDict):
	def __init__(self, path):
		self.path = path
		self.read()
	def read(self):
		if os.path.exists(self.path):
			with open(self.path, 'r') as file:
				self.data = json.load(file)
		else:
			self.data = dict()
	def write(self):
		with open(self.path, 'w') as file:
			json.dump(self.data, file)
	def __delitem__(self, key):
		self.read()
		self.data.pop(key, None)
		self.write()
	def __setitem__(self, key, value):
		self.read()
		self.data[key] = value
		self.write()
	def __getitem__(self, key):
		self.read()
		return self.data[key]
