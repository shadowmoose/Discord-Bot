import discord
import time
from discord.ext import commands
from shadowbot.cogs import Cog
from shadowbot.sql.message import UserMessage


# https://gist.github.com/BananaWagon/068cef8ff640e90d3636d133fa8f72a1
class Manager(Cog):
	known_users = []  # Cache of known user IDs, to prevent useless lookups.

	""" Manages the channel events the bot needs to handle. """
	def __init__(self, bot):
		super().__init__(bot)
		# self.settings.register("test", "default value")

	@commands.Cog.listener()
	async def on_message(self, message: discord.Message):
		if message.author.bot:
			return
		self.check_new_user(message.author)
		msg = UserMessage(
			date=time.time(),
			author=message.author.id,
			server=message.guild.id,
			channel=message.channel.id,
			body=message.content,
		)
		self.sql.add(msg)
		self.sql.commit()

	def check_new_user(self, user):
		""" Add new users to the database, if they don't already exist. """
		if user.id in Manager.known_users:
			return


# When we load the cog, we use the name of the file.
def setup(bot):
	bot.add_cog(Manager(bot))
