import os
import pymysql.cursors
import config
import app

class DB(object):

	def __init__(self):
		self.connection = pymysql.connect(config.host, config.user, config.password, config.db, \
			charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
		self.cur = self.connection.cursor()

	# def __del__(self):
	# 	self.connection.cursor.close()

	def fetchOne(self, sql, params):
		try:
			if params is not False:
				self.cur.execute(sql, [params])
			else:
				self.cur.execute(sql)	
			return self.cur.fetchone()	
		except Exception:
			return False			

	def fetchAll(self, sql, params):
		try:
			self.cur.execute(sql, params)
			return self.cur.fetchall()    
		except Exception:
			return False

	def commit(self, sql, params):
		try:
			self.cur.execute(sql, params)
			self.connection.commit()
			return True
		except Exception:
			print("\n\nCOMMIT FAILED!\n\n")
			return False		

	def delete(self, sql):
		try:
			self.cur.execute(sql)	
			return True
		except Exception:
			return False
