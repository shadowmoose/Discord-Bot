from shadowbot.messages.bot_messages import DeletableMessage, BotMessage, PagedMessage
import discord
from shadowbot.sql.message import BotMessageDB, UserMessageDB
import os
import re


class BotMessageHandler:
	def __init__(self, session):
		self.session = session

	def _all_messages(self, message: discord.Message):
		return [DeletableMessage(message=message), PagedMessage(message=message)]

	def get_handler(self, message: discord.Message):
		bm = self.session.query(BotMessageDB) \
			.filter(BotMessageDB.discord_id == message.id) \
			.first()
		if not bm:
			return None
		for m in self._all_messages(message):
			if m.type == bm.type and m.version == bm.version:
				m.set_data(bm.data)
				return m
		return None

	def store_user_message(self, message: discord.Message, commit_after=True):
		""" Saves the given User discord.Message to the database, and optionally commits after. """
		match = self.session.query(UserMessageDB).filter(UserMessageDB.id == message.id).first()
		if match:
			return False
		msg = UserMessageDB(
			id=message.id,
			date=message.created_at,
			author=message.author.id,
			server=message.guild.id,
			channel=message.channel.id,
			body=message.content,
		)
		self.session.add(msg)
		if commit_after:
			self.session.commit()
		return True

	def add_message_corpus(self, file_path, message: discord.Message):
		""" The Markov User Simulator works much faster on raw file data, so we archive a copy of each guild/user """
		if not os.path.isdir(os.path.dirname(file_path)):
			os.makedirs(os.path.dirname(file_path), exist_ok=True)
		txt = message.clean_content
		if 'http' in txt:
			return
		for t in re.findall(r"(```.+?```)", txt, re.MULTILINE | re.IGNORECASE):
			txt = txt.replace(t, '')
		txt = txt.replace('`', '').strip()
		if len(txt) < 15:
			return
		if txt == '':
			return
		with open(file_path, 'a', encoding='utf-8', errors='ignore') as o:
			o.write(txt + '\n')
