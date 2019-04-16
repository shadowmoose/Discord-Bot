import json
import os


_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../config/config.json"))
settings = {}


def set_file(file):
	global _file_path
	if not file:
		return
	_file_path = os.path.abspath(file)


def save():
	os.makedirs(os.path.dirname(_file_path), exist_ok=True)
	with open(_file_path, 'w') as o:
		json.dump(settings, o, indent=4, sort_keys=True, separators=(',', ': '))


def register_setting(key, default=""):
	if key in settings:
		return False
	settings[key] = default
	save()
	return True


def get(key):
	return settings[key]


def get_settings_base():
	return os.path.dirname(_file_path) + '/'


def load():
	global settings
	print("Loading:", _file_path)
	if not os.path.exists(_file_path):
		save()
	with open(_file_path, 'r') as o:
		settings = json.load(o)


class SettingWrapper:
	taken_name = []

	def __init__(self, module):
		module = module.lower()
		if module in SettingWrapper.taken_name:
			raise Exception("Cannot share class name in settings: %s" % module)
		self.module = module

	def _key(self, key):
		return "%s.%s" % (self.module, key)

	def register(self, key, default):
		""" Registers a default value for the given key. """
		register_setting(self._key(key), default)

	def get(self, key):
		return get(self._key(key))

	def get_save_base(self):
		return get_settings_base()
