from shadowbot.messages.bot_messages import DeletableMessage, BotMessage
import discord
from shadowbot.sql.message import BotMessageDB


class BotMessageHandler:
	def __init__(self, session):
		self.session = session

	def _all_messages(self, message: discord.Message):
		return [DeletableMessage(message)]

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
