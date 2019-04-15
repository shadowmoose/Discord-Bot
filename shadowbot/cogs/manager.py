import discord
from discord.ext import commands
from shadowbot.cogs import Cog
from shadowbot.sql.message import UserMessageDB


# https://gist.github.com/BananaWagon/068cef8ff640e90d3636d133fa8f72a1
class Manager(Cog):
	""" Manages the channel events the bot needs to handle. """
	def __init__(self, bot):
		super().__init__(bot)
		# self.settings.register("test", "default value")

	@commands.Cog.listener()
	async def on_message(self, message: discord.Message):
		if message.author.bot:
			return
		msg = UserMessageDB(
			date=message.created_at,
			author=message.author.id,
			server=message.guild.id,
			channel=message.channel.id,
			body=message.content,
		)
		self.sql.add(msg)
		self.sql.commit()

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
		print(payload.emoji.name)
		if payload.user_id == self.bot.user.id:
			return
		msg = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
		if not msg:
			print("Found no matching bot message for:", payload.message_id)
			return
		bm = self.handler.get_handler(msg)
		if not bm:
			return
		return await bm.handle_reaction(payload.emoji.name)


# When we load the cog, we use the name of the file.
def setup(bot):
	bot.add_cog(Manager(bot))
