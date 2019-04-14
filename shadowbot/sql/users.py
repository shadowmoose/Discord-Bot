from sqlalchemy import Column, String, Integer
import shadowbot.sql as sql


class User(sql.Base):
	__tablename__ = 'user_messages'
	id = Column(Integer, primary_key=True)
	name = Column(Integer, nullable=False)

	def __repr__(self):
		return '<User ID: %s, Name: "%s">' % (self.id, self.name)
