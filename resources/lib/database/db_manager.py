import sqlite3
import threading

from .db_helpers import joinConditions


class DatabaseManager:

	def __init__(self, database):
		self.database = database
		self.dbLock = threading.Lock()

	def lock(func):

		def wrapper(self, *args, **kwargs):

			with self.dbLock:

				try:
					return func(self, *args, **kwargs)
				except sqlite3.Error:
					return

		return wrapper

	@lock
	def count(self, table, condition):
		condition = joinConditions(condition)
		query = f"SELECT COUNT(*) FROM {table} {condition}"
		self._connect()
		self.cursor.execute(query)
		count = self.cursor.fetchone()
		self._close()
		return count[0] if count else 0

	@lock
	def createTable(self, table, columns):
		columns = ", ".join(columns)
		query = f"CREATE TABLE IF NOT EXISTS {table} ({columns})"
		self._connect()
		self.cursor.execute(query)
		self.conn.commit()
		self._close()

	@lock
	def delete(self, table, condition):
		condition = joinConditions(condition)
		query = f"DELETE FROM {table} {condition}"
		self._connect()
		self.cursor.execute(query)
		self.conn.commit()
		self._close()

	@lock
	def insert(self, table, data):
		columns = ", ".join(data.keys())
		placeholders = ":" + ", :".join(data.keys())
		query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
		self._connect()
		self.cursor.execute(query, data)
		self.conn.commit()
		self._close()

	@lock
	def insertMany(self, table, columns, data):
		placeholders = ", ".join("?" * len(columns))
		query = f"INSERT INTO {table} {columns} VALUES ({placeholders})"
		self._connect()
		self.cursor.executemany(query, data)
		self.conn.commit()
		self._close()

	@lock
	def select(self, table, column, condition=None, caseSensitive=True):
		query = f"SELECT {column} FROM {table}"

		if condition:
			query += f" {joinConditions(condition)}"

		if not caseSensitive:
			query += " COLLATE NOCASE"

		self._connect()
		self.cursor.execute(query)
		row = self.cursor.fetchone()
		self._close()
		if row: return row[0]

	@lock
	def selectAll(self, table, condition=None, caseSensitive=True):
		query = f"SELECT * FROM {table}"

		if condition:
			query += f" {joinConditions(condition)}"

		if not caseSensitive:
			query += " COLLATE NOCASE"

		self._connect()
		self.cursor.execute(query)
		rows = self.cursor.fetchall()
		self._close()
		return [dict(row) for row in rows]

	@lock
	def update(self, table, data, condition=None):
		setValues = ", ".join([f"{column} = :{column}" for column in data.keys()])
		query = f"UPDATE {table} SET {setValues}"

		if condition:
			query += f" {joinConditions(condition)}"

		self._connect()
		self.cursor.execute(query, data)
		self.conn.commit()
		self._close()

	def _close(self):
		self.conn.close()

	def _connect(self):
		self.conn = sqlite3.connect(self.database, check_same_thread=False, timeout=15)
		self.conn.row_factory = sqlite3.Row
		self.cursor = self.conn.cursor()
