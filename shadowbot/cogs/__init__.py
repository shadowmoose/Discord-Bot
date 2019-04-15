import shadowbot.util.settings as settings
import shadowbot.sql as sql
from discord.ext import commands
from sqlalchemy.orm.session import Session
from discord.ext.commands.bot import Bot
from shadowbot.messages import BotMessageHandler


class Cog(commands.Cog):
	def __init__(self, bot: Bot):
		self.bot = bot
		self.sql: Session = sql.session()
		self.handler = BotMessageHandler(self.sql)
		self.settings = settings.SettingWrapper(self.__class__.__name__)
		print("Registered Cog:", self.__class__.__name__)
