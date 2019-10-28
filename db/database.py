import sqlite3
import hashlib, binascii, os
from .init_script import init_db

class Database:
  def __init__(self, db_file, *, initialize = False):
    self.connection = sqlite3.connect(db_file)
    self.connection.row_factory = sqlite3.Row
    with self.connection:
      self.connection.execute("PRAGMA foreign_keys = 1")
    if initialize == 'True':
      init_db(self.connection)
    

  async def queryMany(self, query, values, limit=None):
    if isinstance(query, str):
      with self.connection:
        cursor = self.connection.cursor()

        if isinstance(values, list):
          cursor.execute(query, tuple(values))
        elif isinstance(values, dict):
          cursor.execute(query, values)
        else:
          cursor.execute(query)
        
        rows = []
        if (limit):
          rows = cursor.fetchmany(limit)
        else:
          rows = cursor.fetchall()

        columns = []
        if len(rows) > 0:
          columns = rows[0].keys()
          rows = self.formatListOfResults(columns, rows)
        
        return rows
    else:
      raise Exception('No query was given')

  async def queryOne(self, query, values):
    if isinstance(query, str):
      with self.connection:
        cursor = self.connection.cursor()

        if isinstance(values, list):
          cursor.execute(query, tuple(values))
        elif isinstance(values, dict):
          cursor.execute(query, values)
        else:
          cursor.execute(query)
        
        row = cursor.fetchone()
        columns = []
        if row:
          columns = row.keys()
          row = self.formatResult(columns, row)
        return row
    else:
      raise Exception('No query was given')
  
  def formatListOfResults(self, columns, rows):
    list_of_results = [self.formatResult(columns, row) for row in rows]
    return list_of_results

  def formatResult(self, columns, row):
    result = {}
    for column_index, column_name in enumerate(columns):
      result[column_name] = row[column_index]
    return result


      


