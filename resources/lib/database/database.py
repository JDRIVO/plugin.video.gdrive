import sqlite3
import threading


class Database:

	def __init__(self, database):
		self.database = database
		self.cacheLock = threading.Lock()

	def lock(func):

		def wrapper(self, *args, **kwargs):

			with self.cacheLock:
				return func(self, *args, **kwargs)

		return wrapper

	@staticmethod
	def convertToDic(rows):

		if rows:
			return [dict(row) for row in rows]
		else:
			return []

	def connect(self):
		self.conn = sqlite3.connect(self.database, check_same_thread=False, timeout=15)
		self.conn.row_factory = sqlite3.Row
		self.cursor = self.conn.cursor()

	def close(self):
		self.conn.close()

	@lock
	def createTable(self, table, columns):
		columns = ", ".join(columns)
		query = f"CREATE TABLE IF NOT EXISTS {table} ({columns})"
		self.connect()
		self.cursor.execute(query)
		self.conn.commit()
		self.close()

	@lock
	def insert(self, table, data):
		columns = ", ".join(data.keys())
		placeholders = ":" + ", :".join(data.keys())
		query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
		self.connect()
		self.cursor.execute(query, data)
		self.conn.commit()
		self.close()

	@lock
	def insertMany(self, table, columns, data):
		placeholders = ", ".join("?" * len(columns))
		query = f"INSERT INTO {table} {columns} VALUES ({placeholders})"
		self.connect()
		self.cursor.executemany(query, data)
		self.conn.commit()
		self.close()

	@lock
	def tableExists(self, table):
		query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
		self.connect()
		self.cursor.execute(query)
		row = self.cursor.fetchone()
		self.close()
		return row

	@lock
	def valueExists(self, table):
		query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
		self.connect()
		self.cursor.execute(query)
		row = self.cursor.fetchone()
		self.close()
		if row: return row[0]

	@lock
	def select(self, table, column):
		query = f"SELECT {column} FROM {table}"
		self.connect()
		self.cursor.execute(query)
		row = self.cursor.fetchone()
		self.close()
		if row: return row[0]

	@lock
	def selectConditional(self, table, column, condition):
		query = f"SELECT {column} FROM {table} WHERE {condition}"
		self.connect()
		self.cursor.execute(query)
		row = self.cursor.fetchone()
		self.close()
		if row: return row[0]

	@lock
	def selectAll(self, table):
		query = f"SELECT * FROM {table}"
		self.connect()
		self.cursor.execute(query)
		rows = self.cursor.fetchall()
		self.close()
		return self.convertToDic(rows)

	@lock
	def selectAllConditional(self, table, condition):
		query = f"SELECT * FROM {table} WHERE {condition}"
		self.connect()
		self.cursor.execute(query)
		rows = self.cursor.fetchall()
		self.close()
		return self.convertToDic(rows)

	@lock
	def update(self, table, data, condition):
		setValues = ", ".join([f"{column} = :{column}" for column in data.keys()])
		query = f"UPDATE {table} SET {setValues} WHERE {condition}"
		self.connect()
		self.cursor.execute(query, data)
		self.conn.commit()
		self.close()

	@lock
	def delete(self, table, condition):
		query = f"DELETE FROM {table} WHERE {condition}"
		self.connect()
		self.cursor.execute(query)
		self.conn.commit()
		self.close()
