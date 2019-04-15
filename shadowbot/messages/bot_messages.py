import discord
from shadowbot.sql.message import BotMessageDB
import json
from discord.ext import commands
from abc import abstractmethod


class BotMessage:
	def __init__(self, message_type, message=None, sql_session=None):
		self.discord_message: discord.Message = message
		self.type = message_type
		self.sql_session = sql_session
		self.version = 1
		self.data = {}

	def to_sql(self):
		if not self.discord_message:
			raise Exception("Attempting to convert BotMessage without Discord Message! Type:", self.type)
		return BotMessageDB(
			discord_id=self.discord_message.id,
			type=self.type,
			version=self.version,
			date=self.discord_message.created_at,
			server=self.discord_message.guild.id,
			channel=self.discord_message.channel.id,
			data=json.dumps(self.data)
		)

	def set_data(self, data_string):
		self.data = json.loads(data_string)

	async def send(self, ctx: commands.context.Context, **kwargs):
		ret = await self._send(ctx, **kwargs)
		self.sql_session.add(self.to_sql())
		self.sql_session.commit()
		return ret

	@abstractmethod
	async def _send(self, ctx: commands.context.Context, **kwargs):
		pass  # Override this in custom handlers.

	@abstractmethod
	async def handle_reaction(self, emoji):
		return False


class DeletableMessage(BotMessage):
	""" Messages of this type will be sent with an '❌' Emoji, which will delete the message when clicked. """
	delete_emoji = '❌'

	def __init__(self, message: discord.Message = None, sql_session=None):
		super().__init__(message_type=2, message=message, sql_session=sql_session)

	async def handle_reaction(self, emoji):
		if emoji == DeletableMessage.delete_emoji:
			print("Handling delete action for message:", self.discord_message.id)
			await self.discord_message.delete()

	async def _send(self, ctx, **kwargs):
		self.discord_message: discord.Message = await ctx.send(**kwargs)
		await self.discord_message.add_reaction(DeletableMessage.delete_emoji)
		return self.discord_message

