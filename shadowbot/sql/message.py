from sqlalchemy import Column, String, Integer, Float
import shadowbot.sql as sql


class UserMessage(sql.Base):
	__tablename__ = 'user_messages'
	id = Column(Integer, primary_key=True)
	date = Column(Float, nullable=False)
	author = Column(Integer, nullable=False)
	server = Column(Integer, nullable=False)
	channel = Column(Integer, nullable=False)
	body = Column(String, nullable=False)

	def __repr__(self):
		return '<Message ID: %s, Author: "%s", Body: "%s">' % (self.id, self.author, self.body)
