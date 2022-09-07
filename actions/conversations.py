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
from importlib_metadata import NullFinder
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Action
from rasa_sdk.events import SlotSet, ActionExecuted
import logging
import actions.db_connection as dbc
import actions.email as email
from datetime import datetime

# Create a logger to debug things into the shell
_logger  	= logging.getLogger(__name__)

# Create an email object
_email 		= email.email_handler(_logger)

'''
This class handles all processes related to conversations 
'''
class conversations_handler():
	
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

		self.status = {
			'OPEN_AND_UNSUCCESSFUL' : 0,
			'OPEN_AND_SUCCESSFUL' 	: 1,
			'CLOSE_AND_UNSUCCESSFUL': 2,
			'CLOSE_AND_SUCCESSFUL' 	: 3
		}

	'''
	Gets the current conversation or creates a new one into core_support.bot_cnv_conversations
	'''
	def get_or_create(
		self,
	) -> List:

		try:
			cnv_id 	= self._tracker.sender_id
			query 	= f"select count(*) as qt from bot_cnv_conversations where cnv_id = %s"
			result 	= self._db.select_one(query,(cnv_id,))
			
			if("qt" not in result or result["qt"] == 0):
				self.create()
		except:
			error_msg = "Conversation could not be retrieved or created"
			
		return []

	'''
	Stores the conversation into core_support.bot_cnv_conversations
	'''
	def create(
		self,
	) -> List:

		try:
			slots 			= self._tracker.slots
			cnv_id 			= self._tracker.sender_id
			s_id 			= slots["school.s_id"]  if ("school.s_id" in slots) else '0'
			u_id 			= slots["user.u_id"]    if ("user.u_id" in slots)   else '0'
			agent 			= 'teachers_bot'
			status 			= self.status['OPEN_AND_UNSUCCESSFUL']
			forwarded_to 	= ''

			row = (cnv_id, s_id, u_id, agent, status, forwarded_to)
			query = f"""insert ignore into bot_cnv_conversations 
			(cnv_id, s_id, u_id, agent, last_active, status, forwarded_to) 
			values 
			(%s,%s,%s,%s,now(),%s,%s)"""
			
			self._db.insert(query, row)
			
		except:
			error_msg = "Conversation could not be created"
			
		return []

	'''
	Closes the conversation in core_support.bot_cnv_conversations
	'''
	def close(
		self
	) -> List:

		cnv_id 	= self._tracker.sender_id
		row 	= (self.status['CLOSE_AND_SUCCESSFUL'],cnv_id)
		query 	= f"update bot_cnv_conversations set `status` = %s where cnv_id = %s"

		self._db.update(query, row)

		return []

	'''
	Returns the relevant conversation history data from the _tracker
	'''
	def get_history(
		self,
	) -> List:
		cnv_history 		= []

		for e in self._tracker.events[::-1]:

			if(e["event"] in ['user','bot']):

				row = {"event" : e["event"]}

				if("timestamp" in e):
					row["timestamp"]    = e["timestamp"]
				
				# Get the text of the message
				if("text" in e):
					msg = e["text"]
				elif("data" in e and "custom" in e["data"]):
					msg = e["data"]["custom"]

				# Discard EXTERNAL messages like when triggering set_variables
				if(msg is not None and str(msg).startswith("EXTERNAL: ")): 
					continue
				
				row["text"] = msg

				retrieval_intent = "default"
				
				if("message_id" in e):
					row["message_id"] = e["message_id"]

				if(
					e["event"] == 'user'
					and "parse_data" in e
					and "response_selector" in e["parse_data"]
					and retrieval_intent in e["parse_data"]["response_selector"]
					and "response" in e["parse_data"]["response_selector"][retrieval_intent]
				): #The user is speaking
					
					response = e["parse_data"]["response_selector"][retrieval_intent]["response"]
					row["intent"]       = response["intent_response_key"]
					row["confidence"]   = response["confidence"]
				
				elif(
					e["event"] == 'bot'
					and "metadata" in e 
					and "utter_action" in e["metadata"]
				): #The bot is speaking

					row["utter_action"] = e["metadata"]["utter_action"]

				cnv_history.append(row)

		return cnv_history

	'''
	Returns the relevant conversation history data from the _tracker in a human readable format
	'''
	def get_human_readable(
		self,
		params = {}
	):
		slots 			= self._tracker.slots
		readable_cnv 	= ''
		user_name 		= 'Usuario'
		lb 				= "\n"

		if("target" in params and params["target"] == 'email'):
			lb = "<br/>"

		if("user.first_name" in slots and slots["user.first_name"] is not None):
			user_name   = slots["user.first_name"]

		# Process the history to be human readable from the beginning, to the end
		cnv_history 	= self.get_history()
		cnv_straight 	= cnv_history[::-1]
		cnv_section 	= cnv_straight

		if("messages_qt" in params):
			messages_qt = int(params["messages_qt"])
			
			pos_end 	= len(cnv_straight) + 1
			pos_start 	= max(1,pos_end - messages_qt)

			cnv_section = cnv_straight[pos_start:pos_end]

		for reply in cnv_section:

			if(reply["text"] is not None):
				
				reply_date = str(datetime.fromtimestamp(reply["timestamp"]))
				reply_date = reply_date[0:19]

				if(reply["event"] == 'user'):
					readable_cnv += f"{reply_date} - <b>{user_name}</b>:" + lb + reply["text"] + lb + lb

				elif(reply["event"] == 'bot'):
					readable_cnv += f"{reply_date} - <b>Bot</b>: " + lb + reply["text"] + lb + lb

		if("target" in params and params["target"] == 'email'):
			readable_cnv = "<p align='left'>" + readable_cnv + "</p>"

		return readable_cnv

	'''
	Sends a copy of the current conversation to a given email in params.recipient_email
	'''
	def send_to_email(
		self,
		params,
	):

		slots 			= self._tracker.slots
		s_id 			= '--'
		u_id 			= '--'
		user_full_name 	= '--'
		user_email 		= '--'
		recipient_email = 'soporte@ciudadeducativa.com'
		headers 		= None

		if("recipient_email" in params and params["recipient_email"] is not None):
			recipient_email 	= params["recipient_email"]

		if("headers" in params and params["headers"] is not None):
			headers 			= params["headers"]

		if("user.first_name" in slots and slots["user.first_name"] is not None):
			user_full_name 		= str(slots["user.first_name"]) + ' ' + str(slots["user.last_name"])

		if("user.email" in slots and slots["user.email"] is not None):
			user_email 			= slots["user.email"]
		
		if("user.u_id" in slots and slots["user.u_id"] is not None):
			u_id 				= slots["user.u_id"]
		
		if("school.s_id" in slots and slots["school.s_id"] is not None):
			s_id 				= slots["school.s_id"]

		# Send message to {recipient_email}

		readable_cnv 	= self.get_human_readable({
			"messages_qt" 	: 20,
			"target" 		: "email"
		})

		body_intro 		= f"""El usuario estuvo hablando con Edy y solicitó enviar una copia de la conversación
		<br/>Nombre completo: {user_full_name} 
		<br/>Institución: {s_id}
		<br/>Usuario ID: {u_id}
		<br/>Correo electrónico: {user_email}
		"""

		body_intro_user = f"""Esta es una copia de la conversación enviada a {recipient_email}
		<br/>Nombre completo: {user_full_name} 
		<br/>Institución: {s_id}
		<br/>Usuario ID: {u_id}
		<br/>Correo electrónico: {user_email}
		"""

		body 			= body_intro
		body 			+= "\n"
		body 			+= readable_cnv

		params = {
			"headers"   : headers,
			"recipients": recipient_email,
			"subject"   : f"{s_id}:{u_id} {user_full_name} - Edy te envía una conversación ",
			"body"      : body,
		}

		if(user_email != '--'):
			params["email_from"] = user_email
		
		if(user_full_name != '--'):
			params["name_from"] = user_full_name

		_email.send(params)

		# Send a copy of the email to the user

		if(user_email != '--'):
			params["recipients"] 	= user_email

			body_user 		= body_intro_user
			body_user 		+= "\n"
			body_user 		+= readable_cnv

			params["body"] 	= body_user
			_email.send(params)


		return []

