from discord.ext import commands
from shadowbot.cogs import Cog
import random
import re


class DiceRoller(Cog):
	""" Dice rolling module """
	def __init__(self, bot):
		super().__init__(bot)

	@commands.command()
	async def roll(self, ctx: commands.context.Context, *args):
		"""Roll some dice!
		Usage:
			roll [#x] (eg: "d12" or "12")
			Example: roll 2xD20
			Pass "roll character" to autoroll all stats. Automatically discards the lowest roll of 4, for characters."""
		if not args:
			return "No roll values provided!"
		if 'char' in ''.join(args):
			txt, troll = self.roll_character()
		else:
			vals = self.roll_args(args)
			txt, troll = self.build_response(vals)
		msg = await ctx.send(ctx.author.mention+"\n"+txt)
		if troll:
			await msg.add_reaction(self.pick_bad_emoji())  # add some insult to injury.

	def roll_args(self, args):
		args = [a.strip(' ,') for a in args if a]
		rolls = []
		for a in args:
			for s in a.split(','):
				rolls.append(s.strip(', '))
		vals = {}
		for r in rolls:
			if not r:
				continue
			va = self.roll_txt(r)
			for k, v in va.items():
				if k not in vals:
					vals[k] = []
				vals[k].extend(v)
		return vals

	def roll_txt(self, txt):
		vals = {}
		multi = re.match(r"(\d+)(\D+)(\d+)", txt)
		if multi:
			mx = min(1000, int(multi.group(3)))
			amount = min(int(multi.group(1)), 20)
			if mx not in vals:
				vals[mx] = []
			for i in range(amount):
				vals[mx].append(random.randrange(1, mx+1))
		else:
			try:
				mx = min(1000, int(txt))
				vals[mx] = [random.randrange(1, mx+1)]
			except ValueError:
				pass
		return vals

	def build_response(self, vals):
		tot = 0
		roll_count = 0
		troll = False
		out = '__**Rolls:**__\n'
		for k, r in vals.items():
			out += '     **d%s [%s]:**  ' % (k, len(r))
			out += ', '.join(str(v) for v in r)
			roll_count += len(r)
			t = sum(r)
			tot += t
			if k == 20 and 1 in r:
				troll = True
			out += " -- *Total: %s*\n" % t
		out += '__**Total:**__ %s' % tot
		if roll_count == 1:
			out = '__**Roll:**__ %s' % tot
		if roll_count > 50:
			out = "*Unable to roll that many at once!*"
		if roll_count > 5:
			troll = False
		return out, troll

	def roll_character(self):
		rolls = {}
		for i in range(1, 7):
			key = 'Stat %s' % i
			for x in range(0, 4):
				if key not in rolls:
					rolls[key] = []
				rolls[key].append(random.randint(1, 6))
			rolls[key] = sorted(rolls[key], reverse=True)
		out = '__**Rolls:**__\n'
		total = 0
		highest = 0
		for k, v in rolls.items():
			out += '     **%s:**  %s,  [%s] -- *Total: %s*\n' % \
				(k, ', '.join(str(m) for m in v[0:3]), ', '.join(str(m) for m in v[3:]), sum(v[0:3]))
			total += sum(v[0:3])
			highest = max(highest, sum(v[0:3]))
		out += '__**Total:**__ %s' % total
		return out, (total <= 72 and highest <= 15)

	def pick_bad_emoji(self):
		return random.choice('👌💩😆😝😈😭😹💯👍😹😈🙃😉😱🖕')


# When we load the cog, we use the name of the file.
def setup(bot):
	bot.add_cog(DiceRoller(bot))
