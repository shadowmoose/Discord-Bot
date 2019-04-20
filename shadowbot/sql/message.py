from sqlalchemy import Column, String, Integer, DateTime
import sql


class UserMessageDB(sql.Base):
	__tablename__ = 'user_messages'
	id = Column(Integer, primary_key=True)
	date = Column(DateTime, nullable=False)
	author = Column(Integer, nullable=False)
	server = Column(Integer, nullable=False)
	channel = Column(Integer, nullable=False)
	body = Column(String, nullable=False)

	def __repr__(self):
		return '<Message ID: %s, Author: "%s", Body: "%s">' % (self.id, self.author, self.body)


class BotMessageDB(sql.Base):
	__tablename__ = 'bot_messages'
	discord_id = Column(Integer, primary_key=True, nullable=False)
	type = Column(Integer, nullable=False)
	version = Column(Integer, nullable=False)
	date = Column(DateTime, nullable=False)
	server = Column(Integer, nullable=False)
	channel = Column(Integer, nullable=False)
	data = Column(String, nullable=False)
