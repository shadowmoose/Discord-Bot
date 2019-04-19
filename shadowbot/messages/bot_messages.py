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


class PagedMessage(BotMessage):
	def __init__(self, dict_data=None, start_key=None, content=None, message: discord.Message = None, sql_session=None):
		super().__init__(message_type=3, message=message, sql_session=sql_session)
		if dict_data is None:
			dict_data = dict()
		self.start_key = start_key
		if not start_key and dict_data:
			self.start_key = list(dict_data.keys())[0]
		self.data['pages'] = dict_data
		self.data['content'] = content

	async def _send(self, ctx: commands.context.Context, **kwargs):
		self.discord_message = await ctx.send(
			content=self.data['content'],
			embed=self._dict_to_embed(self.data['pages'][self.start_key])
		)
		await self._send_key_reations()
		return self.discord_message

	async def handle_reaction(self, emoji):
		if emoji in self.data['pages']:
			await self.discord_message.edit(content=self.data['content'], embed=self._dict_to_embed(self.data['pages'][emoji]))
			await self.discord_message.clear_reactions()
			await self._send_key_reations()

	async def _send_key_reations(self):
		for emoji, v in self.data['pages'].items():
			await self.discord_message.add_reaction(emoji)

	def _dict_to_embed(self, d):
		def g(name, default=''):
			if name in d:
				return d[name]
			return default
		embed = discord.Embed(title=g('title'), description=g('desc'), colour=g('color', 0x98FB98))
		for f in g('fields', default=[]):
			def gf(name, default=''):
				if name in f and f[name]:
					return f[name]
				return default
			embed.add_field(name=gf('name', 'empty'), value=gf('value', '...'), inline=gf('inline', default=False))
		return embed
