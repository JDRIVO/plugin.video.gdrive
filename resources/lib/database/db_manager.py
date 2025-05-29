import sqlite3
import threading

import xbmc

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
				except sqlite3.Error as e:
					xbmc.log(f"gdrive error: {e}", xbmc.LOGERROR)
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
		query = f"INSERT OR REPLACE INTO {table} {columns} VALUES ({placeholders})"
		self._connect()
		self.cursor.executemany(query, data)
		self.conn.commit()
		self._close()

	@lock
	def select(self, table, column="*", condition=None, caseSensitive=True, fetchAll=True):
		query = f"SELECT {column} FROM {table}"

		if condition:
			query += f" {joinConditions(condition)}"

		if not caseSensitive:
			query += " COLLATE NOCASE"

		self._connect()
		self.cursor.execute(query)

		if fetchAll:
			rows = self.cursor.fetchall()
			data = [dict(r) for r in rows] if column == "*" else [r[0] for r in rows]
		else:
			data = self.cursor.fetchone()

			if data:
				data = dict(data) if column == "*" else data[0]

		self._close()
		return data

	@lock
	def update(self, table, data, condition=None):
		setValues = ", ".join(f"{column} = :{column}" for column in data.keys())
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
