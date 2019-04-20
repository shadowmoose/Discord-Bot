import discord
from discord.ext import commands
from cogs import Cog
from messages.bot_messages import DeletableMessage


# https://gist.github.com/BananaWagon/068cef8ff640e90d3636d133fa8f72a1
class SimpleCog(Cog, command_attrs=dict(hidden=True)):
	""" Embed Module """
	def __init__(self, bot):
		super().__init__(bot)
		# self.settings.register("test", "default value")

	@commands.command(pass_context=True, name='embeds')
	#  @commands.guild_only()
	async def example_embed(self, ctx: commands.context.Context):
		"""Demonstrate embeds.
		Have a play around and visit the Visualizer."""

		embed = discord.Embed(title='Example Embed',
							  description='Showcasing the use of Embeds...\nSee the visualizer for more info.',
							  colour=0x98FB98)
		embed.set_author(name='MysterialPy',
						 url='https://gist.github.com/MysterialPy/public',
						 icon_url='http://i.imgur.com/ko5A30P.png')
		embed.set_image(url='https://cdn.discordapp.com/attachments/84319995256905728/252292324967710721/embed.png')

		embed.add_field(name='Embed Visualizer', value='[Click Here!](https://leovoel.github.io/embed-visualizer/)')
		embed.add_field(name='Command Invoker', value=ctx.message.author.mention)
		embed.set_footer(text='Made in Python with discord.py@rewrite', icon_url='http://i.imgur.com/5BFecvA.png')
		dmsg = DeletableMessage(sql_session=self.sql)
		await dmsg.send(ctx, content='**A simple Embed for discord.py@0.16.12 in cogs.**', embed=embed)

	@commands.command()
	async def echo(self, ctx, arg):
		""" Demonstrate passing in positional arguments. """
		await ctx.send(arg)


# When we load the cog, we use the name of the file.
def setup(bot):
	bot.add_cog(SimpleCog(bot))
