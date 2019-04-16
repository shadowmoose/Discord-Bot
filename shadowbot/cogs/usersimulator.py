from discord.ext import commands
from shadowbot.cogs import Cog
from shadowbot.util import settings
import os
import markovify
import random
import discord
'''
# import spacy
# nlp = spacy.load("en_core_web_sm")
class POSifiedText(markovify.Text):
	def word_split(self, sentence):
		return ["::".join((word.orth_, word.pos_)) for word in nlp(sentence)]

	def word_join(self, words):
		sentence = " ".join(word.split("::")[0] for word in words)
		return sentence
'''


class UserSimulator(Cog):
	""" Dice rolling module """
	def __init__(self, bot):
		super().__init__(bot)
		self.settings.register('allow_simulation', True)

	@commands.Cog.listener()
	@commands.guild_only()
	async def on_message(self, message: discord.Message):
		""" Track & save a raw-text version of all user messages, for faster Markov generation. """
		if not self.settings.get('allow_simulation'):
			return
		if message.author.bot or not message.guild:
			return
		self.handler.add_message_corpus(self.message_to_path(message), message)

	@commands.command()
	@commands.guild_only()
	async def sim(self, ctx: commands.context.Context, user, sentences=1):
		""" Simulate the given user
		Use as "sim [username] [sentence_count]"
		"""
		if not self.settings.get('allow_simulation'):
			await ctx.send("User simulation has been disabled for this bot, by the owner.")
			return
		line_count = min(10, int(float(sentences)) if sentences else 1)
		target = None
		for member in ctx.guild.members:
			if member.bot:
				continue
			low = user.lower()
			if low in member.name.lower() or (member.nick and low in member.nick.lower()):
				target = member
				break
		if not target:
			await ctx.send("Unable to locate a matching user!")
			return
		file = self.message_to_path(ctx.message)
		if not os.path.isfile(file):
			await ctx.send("Unable to find user data!")
			return
		with open(file, 'r', encoding='utf-8', errors='ignore') as o:
			text_model = markovify.NewlineText(o, retain_original=False)
		out = ''
		for i in range(line_count):
			sent = text_model.make_sentence().strip()
			out += ' ' + sent
			if not any(sent.endswith(p) for p in ['.?!:;,']):
				out += random.choice('.....?!')
		em = discord.Embed(description=out, color=target.top_role.color)
		em.set_author(name=target.name, icon_url=target.avatar_url)
		await ctx.send(embed=em)

	def message_to_path(self, message: discord.Message):
		""" Build the filepath to save user messages to, for a given message. """
		base = settings.get_settings_base() + '/data/messages/%s/users/' % message.guild.id
		file = base + '%s.txt' % message.author.id
		return file


# When we load the cog, we use the name of the file.
def setup(bot):
	bot.add_cog(UserSimulator(bot))
