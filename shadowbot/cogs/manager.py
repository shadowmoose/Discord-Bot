import discord
from discord.ext import commands
from shadowbot.cogs import Cog
from shadowbot.cogs.user_simulator import UserSimulator
import defusedxml
import time


defusedxml.defuse_stdlib()  # Monkey-patch all XML libs.


# https://gist.github.com/BananaWagon/068cef8ff640e90d3636d133fa8f72a1
class Manager(Cog, command_attrs=dict(hidden=True)):
	""" Manages the channel events the bot needs to handle. """
	def __init__(self, bot):
		super().__init__(bot)
		# self.settings.register("test", "default value")

	@commands.Cog.listener()
	@commands.guild_only()
	async def on_message(self, message: discord.Message):
		if message.author.bot or not message.guild:
			return
		self.handler.store_user_message(message, commit_after=True)

	@commands.Cog.listener()
	@commands.guild_only()
	async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
		if payload.user_id == self.bot.user.id or not payload.guild_id:
			return
		print('Emoji:', payload.emoji.name)
		msg = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
		if not msg:
			print("Found no matching bot message for:", payload.message_id)
			return
		bm = self.handler.get_handler(msg)
		if not bm:
			print("Found no valid handler for the message reacted to!")
			return
		return await bm.handle_reaction(payload.emoji.name)

	@commands.command()
	@commands.is_owner()
	@commands.guild_only()
	async def load_user_messages(self, ctx: commands.context.Context, build_user_corpus=True):
		""" Load all User Messages into the DB - this is slow & Admin Only. """
		start = time.time()
		msg: discord.Message = await ctx.send("Rebuilding User text models in Database...")
		found = 0
		sent = [msg]
		async with ctx.typing():
			for guild in self.bot.guilds:
				for ch in guild.text_channels:
					permission = ch.permissions_for(guild.get_member(self.bot.user.id))
					if not permission.read_messages:
						print("Skipping unreadable channel:", ch.name)
						continue
					msg = await ctx.send("Scanning guild: '%s'  ->   Channel: [%s]..." % (guild.name, ch.name))
					sent.append(msg)
					print("Scanning guild: %s  ->   Channel: %s" % (guild.name, ch.name))
					async for message in ch.history(limit=None):
						if message.author.bot:
							continue
						if self.handler.store_user_message(message, commit_after=False):
							found += 1
							if build_user_corpus:
								path = UserSimulator.message_to_path(message)
								self.handler.add_message_corpus(file_path=path, message=message)
					print("\t+Finished at:", round(time.time() - start, 2))
		self.sql.commit()
		for msg in sent:
			await msg.delete()
		elapsed = round(time.time() - start, 2)
		await ctx.send("Gathered all User text data. Found %s new messages in %s seconds." % (found, elapsed))


# When we load the cog, we use the name of the file.
def setup(bot):
	bot.add_cog(Manager(bot))
