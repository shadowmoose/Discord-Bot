import discord
from discord.ext import commands
from os import listdir
import sys
from os.path import isfile, join, dirname, abspath
import traceback
import argparse
from util import settings
import sql

# INVITE: https://discordapp.com/api/oauth2/authorize?client_id=566711902449827860&permissions=133692864&scope=bot

__version__ = '2.0.1'

parser = argparse.ArgumentParser(
	description="ShadowBot Discord Bot!")
parser.add_argument("--token", help="Discord Client Secret", type=str, metavar='', default=None)
parser.add_argument("--config", help="Config file path", type=str, metavar='', default=None)
args, unknown_args = parser.parse_known_args()

settings.set_file(args.config)
settings.load()
settings.register_setting("token", args.token)
settings.register_setting("database", settings.get_settings_base() + '/discord-db.sqldb')

sql.init(settings.get("database"))


def get_prefix(_bot, message):
	"""A callable Prefix for our bot. This could be edited to allow per server prefixes."""
	prefixes = ['>', '/']

	# Check to see if we are outside of a guild. e.g DM's etc.
	if not message.guild:
		# Only allow ? to be used in DMs
		return '?'

	# If we are in a guild, we allow for the user to mention us or use any of the prefixes in our list.
	return commands.when_mentioned_or(*prefixes)(_bot, message)


# This is the directory all are located in.
cogs_base = 'cogs'
cogs_dir = abspath(dirname(__file__) + '/' + cogs_base)
sys.path.insert(0, cogs_dir)
bot = commands.Bot(command_prefix=get_prefix, description='ShadowBot v%s' % __version__, case_insensitive=True)

# Here we load our extensions(cogs) that are located in the cogs directory. Any file in here attempts to load.
if __name__ == '__main__':
	for extension in [f.replace('.py', '') for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))]:
		if '_init_' in extension:
			continue
		try:
			bot.load_extension(extension)
		except (discord.ClientException, ModuleNotFoundError):
			print(f'Failed to load extension {extension}.')
			traceback.print_exc()


@bot.event
async def on_ready():
	"""http://discordpy.readthedocs.io/en/rewrite/api.html#discord.on_ready"""
	print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
	await bot.change_presence(activity=discord.Game(name="ShadowBot v%s" % __version__))
	print(f'Successfully logged in and booted...!')


token = settings.get("token")
if args.token:
	token = args.token
	print("+Using command-line token!")
if not token:
	print("No token set! Please edit the generated config file!")
	sys.exit(1)
bot.run(settings.get("token"), bot=True, reconnect=True)
