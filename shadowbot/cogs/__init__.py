import shadowbot.util.settings as settings
import shadowbot.sql as sql
from discord.ext import commands
from sqlalchemy.orm.session import Session
from discord.ext.commands.bot import Bot


class Cog(commands.Cog):
	def __init__(self, bot: Bot):
		self.bot = bot
		self.sql: Session = sql.session()
		self.settings = settings.SettingWrapper(self.__class__.__name__)
		print("Registered Cog:", self.__class__.__name__)
