'''
--------------------------------------------------------------------
EdyBot - Virtual assistant for teachers of Ciudad Educativa
Developed by Camilo Rivillas - camilorivillas@nusoft.com.co
Núcleo Software SAS
Last update 2022-09-06

Final Project of the Master in Artificial Intelligence UNIR 2022.
The partial or total reproduction and use of this code is permitted
as long as the author is credited
--------------------------------------------------------------------
EdyBot - Asistente virtual para maestros de Ciudad Educativa
Desarrollado por Camilo Rivillas - camilorivillas@nusoft.com.co
Núcleo Software SAS
Última actualización 2022-09-06

Trabajo Final de la Maestría en Inteligencia Artificial UNIR 2022.
La reproducción y uso parcial o total de este código está permitido
siempre y cuando se de crédito al autor
--------------------------------------------------------------------
'''

from typing import Any, Text, Dict, List
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from sqlalchemy import null
import os
from dotenv import load_dotenv
load_dotenv()

'''
This class handles connection to MySQL database
'''
class db_handler():
	
	'''
	Class constructor
	'''
	def __init__(
		self,
		_logger,
	):
		self._logger  = _logger
		
		ADB_HOST = str(os.getenv('HOST'))
		ADB_DATA = str(os.getenv('DATA'))
		ADB_USER = str(os.getenv('USER'))
		ADB_PASS = str(os.getenv('PASS'))

		self._con = mysql.connector.connect(host=ADB_HOST,database=ADB_DATA,user=ADB_USER,password=ADB_PASS)
		self._cur = self._con.cursor(dictionary=True)

	'''
	Executes a query to select one record from the database
	'''
	def select_one(
		self,
		query,
		params = ()    
	):
		result = {}

		try:
			if(params is None or len(params) == 0):
				self._cur.execute(query)
			else:
				self._cur.execute(query, params)
			result = self._cur.fetchone()
			
		except mysql.connector.Error as err:
			result = {}
			self._logger.warning("Error: db_handler.select_one() has failed.")
			self._logger.warning(err)
			self._logger.warning(self._cur._executed)

		return result


	'''
	Executes a query to select several records from the database
	'''
	def select_many(
		self,
		query,
		params = (),
		index = None    
	):
		result = {}

		try:
			if(params is None or len(params) == 0):
				self._cur.execute(query)
				print(query)
			else:
				self._cur.execute(query, params)
			
			tmp_result = self._cur.fetchall()

			if(index is not None):
				for row in tmp_result:
					result[row[index]] = row
			else:
				result = tmp_result
	
		except mysql.connector.Error as err:
			result = {}
			self._logger.warning("Error: db_handler.select_many() has failed.")
			self._logger.warning(err)
			self._logger.warning(self._cur._executed)

		return result

	'''
	Inserts a record into a table in the database
	'''
	def insert(
		self,
		query,
		params = ()
	):
		try:
			if(params is None or len(params) == 0):
				self._cur.execute(query)
			else:
				self._cur.execute(query, params)
			result = self._con.commit()
			
		except mysql.connector.Error as err:
			result = False
			self._logger.warning("Error: db_handler.insert() has failed.")
			self._logger.warning(err)
			self._logger.warning(self._cur._executed)

		return result
	
	'''
	Inserts a record into a table in the database
	'''
	def insert_many(
		self,
		query,
		params = ()
	):
		try:
			if(params is None or len(params) == 0):
				self._cur.executemany(query)
			else:
				self._cur.executemany(query, params)
			result = self._con.commit()
			
		except mysql.connector.Error as err:
			result = False
			self._logger.warning("Error: db_handler.insert() has failed.")
			self._logger.warning(err)
			self._logger.warning(self._cur._executed)

		return result

	'''
	Updates a record into a table in the database
	'''
	def update(
		self,
		query,
		params = ()
	):
		self._logger.warning('updating')

		try:
			if(params is None or len(params) == 0):
				self._cur.execute(query)
			else:
				self._cur.execute(query, params)
			result = self._con.commit()
			self._logger.warning(self._cur._executed)

		except mysql.connector.Error as err:
			result = False
			self._logger.warning("Error: db_handler.update() has failed.")
			self._logger.warning(err)
			self._logger.warning(self._cur._executed)

		return result

	'''
	Deletes a record from a table in the database
	'''
	def delete(
		self,
		query,
		params = ()
	):
		try:
			if(params is None or len(params) == 0):
				self._cur.execute(query)
			else:
				self._cur.execute(query, params)
			result = self._con.commit()

		except mysql.connector.Error as err:
			result = False
			self._logger.warning("Error: db_handler.delete() has failed.")
			self._logger.warning(err)
			self._logger.warning(self._cur._executed)

		return result

