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
import actions.conversations as cnv
import actions.db_connection as dbc
from sqlalchemy import null
from datetime import datetime

'''
This class handles all processes related to conversations 
'''
class replies_handler():
	
	'''
	Class constructor
	'''
	def __init__(
		self,
		_logger,
		_tracker,
		_db
	):
		self._logger 	= _logger
		self._tracker 	= _tracker
		self._db 		= _db

	'''
	Stores the conversation into core_support.bot_cnv_conversations
	'''
	def log_usefulness(
		self,
		useful 		= 'calculate',
		question 	= '',
		question_position = 2
	) -> List:

		_logger 			= self._logger
		_tracker 			= self._tracker
		_db 				= self._db

		# Get last utterance

		latest_user_intent 	= _tracker.latest_message["intent"]["name"]
		latest_user_msg 	= _tracker.latest_message["text"]
		cnv_id 				= _tracker.sender_id
		slots 				= _tracker.slots
		s_id 				= slots["school.s_id"] 	if ("school.s_id" in slots and slots["school.s_id"] is not None) 	else '0'
		u_id 				= slots["user.u_id"] 	if ("user.u_id" in slots and slots["user.u_id"] is not None) 		else '0'

		# Get conversation history
		_cnv 				= cnv.conversations_handler(_logger,_tracker,_db)
		cnv_history 		= _cnv.get_history()

		reply_date 			= null
		cnv_recent_history 	= cnv_history[1:7]

		if(
			question == ''
			and
			cnv_recent_history[question_position] is not None
		):
			if("text" in cnv_recent_history[question_position]):
				question = cnv_recent_history[question_position]['text']

		#_logger.warning('question: ' + question)

		str_cnv_recent_history 	= str(cnv_recent_history)

		'''
		Emoticons must be removed from cnv history. Otherwise, mysql will raise an error: 'Incorrect string value...'
		@todo: It can be fixed with utf8mb4
		https://mathiasbynens.be/notes/mysql-utf8mb4#character-sets
		'''

		str_cnv_recent_history 	= str_cnv_recent_history.encode("ascii", "ignore")
		str_cnv_recent_history 	= str_cnv_recent_history.decode()

		intent              = null
		confidence          = null

		if(useful == 'calculate'):
			useful              = latest_user_intent

		#_logger.warning('useful: ' + useful)

		for evt in cnv_recent_history:
			
			faq_or_chitchat = False

			if(
				"intent" in evt
				and
				(
					str(evt["intent"]).startswith("faq/")
					or
					str(evt["intent"]).startswith("chitchat/")
				)
			):
				faq_or_chitchat = True

			if(
				reply_date is null 
				and "timestamp" in evt
			):
				reply_date = datetime.fromtimestamp(evt["timestamp"])
				#_logger.warning('reply_date: ' + str(reply_date))

			if(
				intent is null 
				and "intent" in evt
				and faq_or_chitchat
			):
				intent = evt["intent"]
				#_logger.warning('intent: ' + str(intent))
			
			if(
				confidence is null
				and "intent" in evt
				and faq_or_chitchat
			):
				confidence = evt["confidence"]
				#_logger.warning('confidence: ' + str(confidence))
				break

		# Get or create the conversation
		_cnv.get_or_create()

		#_logger.warning('conversation created')

		if(
			intent is not null
			and confidence is not null
		):
			#_logger.warning('inserting into bot_cnv_replies')
			# Store the conversation latest replies and usefulness into core_support.bot_cnv_replies
			row = (cnv_id, s_id, u_id, reply_date, question, str_cnv_recent_history, intent, confidence, useful)

			query = f"""insert into bot_cnv_replies 
			(cnv_id, s_id, u_id, reply_date, question, cnv_history, intent, confidence, useful) 
			values 
			(%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

			_db.insert(query, row)
		
		#_logger.warning('end')


		return []