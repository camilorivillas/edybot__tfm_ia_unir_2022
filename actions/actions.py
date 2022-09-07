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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from datetime import datetime
from xmlrpc.client import Boolean
from sqlalchemy import null
from typing import Any, Text, Dict, List
import random
import logging

# Custom libraries
import actions.conversations as cnv
import actions.db_connection as dbc
import actions.conditions as cnd
import actions.answers as ans
import actions.replies as rpl
import actions.intents as int

# RASA libraries
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Action
from rasa_sdk.events import SlotSet, ActionExecuted

# Create a logger to debug things into the shell
_logger 	= logging.getLogger(__name__)

# Create a database object
_db 		= dbc.db_handler(_logger)

'''
Handles the action of saying 'Hello' to the user
'''
class utter_greet(Action):
	
	'''
	Returns the name of the action. Required by RASA
	'''
	def name(self) -> Text:
		return "greet"
	
	'''
	Executes the custom code for this action.
	'''
	def run(
		self, 
		_dispatcher, 
		_tracker, 
		_domain: Dict[Text, Any]
	) -> List[Dict[Text,Any]]:
		
		events 			= []
		now         	= datetime.now()
		current_hm  	= now.strftime("%H%M")
		slots       	= _tracker.slots
		_ans 			= ans.answers_handler(_logger,_tracker,_domain,_db)

		user_name 		= ''

		if(
			"user.first_name" in slots 
			and slots["user.first_name"] is not None
		):
			user_name = " " + str(slots["user.first_name"])

		msg = _ans.get_one_expression("utter_good_day")

		if(current_hm >= "1800"):
			msg = _ans.get_one_expression("utter_good_night")
		
		elif(current_hm >= "1200"):
			msg = _ans.get_one_expression("utter_good_afternoon")

		msg = msg.format(user_name=user_name)

		_dispatcher.utter_message(text=msg)
		
		return events

'''
Handles the action of saying 'Goodbye' to the user
'''
class utter_goodbye(Action):
	
	'''
	Returns the name of the action. Required by RASA
	'''
	def name(self) -> Text:
		return "goodbye"
	
	'''
	Executes the custom code for this action.
	'''
	def run(
		self, 
		_dispatcher, 
		_tracker, 
		_domain: Dict[Text, Any]
	) -> List[Dict[Text,Any]]:

		_cnv            = cnv.conversations_handler(_logger,_tracker,_db)
		_ans 			= ans.answers_handler(_logger,_tracker,_domain,_db)
		
		# Send the user a satisfaction survey url
		msg             = _ans.get_one_expression("utter_please_answer_this_survey")
		_dispatcher.utter_message(text=msg)

		# Say goodbye
		now             = datetime.now()
		current_hour    = now.strftime("%H%m")
		
		farewell        = _ans.get_one_expression("utter_have_a_good_day")

		if(current_hour >= "1800"):
			farewell    = _ans.get_one_expression("utter_have_a_good_night")
		
		elif(current_hour >= "1200"):
			farewell    = _ans.get_one_expression("utter_have_a_good_afternoon")

		msg = _ans.get_one_expression("utter_goodbye")
		msg += farewell

		# In the json message, a callback.action must be included to request the PMS to end the conversation
		json_msg = {
			"success"         : True,
			"data"            : {
				"text"            : msg,
				"callback"        : {
					"action" : "cnv.end",
				}
			}
		}
				
		_dispatcher.utter_message(json_message=json_msg)

		# Set conversation status as `closed`
		_cnv.close()

		return []

'''
Sets the variables received through API
'''
class set_variables(Action):
	
	'''
	Returns the name of the action. Required by RASA
	'''
	def name(self) -> Text:
		return "set_variables"
	
	'''
	Executes the custom code for this action.
	'''
	async def run(
		self,
		_dispatcher: CollectingDispatcher,
		_tracker: Tracker,
		_domain: Dict[Text, Any],
	) -> Dict[Text, Any]:

		_cnv            = cnv.conversations_handler(_logger,_tracker,_db)

		_logger.info("Executing set_variables()")

		events      = []
		slots       = []
		sender_id   = _tracker.sender_id

		events.append(SlotSet(key="cnv.one_faq_received", value="0"))

		'''
		Check from end to beginning, 
		the first event of type 'user' whose intent 
		is 'set_variables' having 'entities' passed as argument
		'''
		for e in _tracker.events[::-1]:

			if(
				e["event"] == 'user'
				and "parse_data" in e
				and "intent" in e["parse_data"]
				and e["parse_data"]["intent"]["name"] == 'set_variables'
				and "entities" in e["parse_data"]
			):
				at_least_one_slot = False
				slots 	= e["parse_data"]["entities"]
				ar_rows = []

				for slot in slots:
					entity  = slot['entity']
					value   = slot['value']

					if value is not None:
						at_least_one_slot = True

						row = (sender_id,entity,value)
						ar_rows.append(row)
						
				# Save the variable into the database
				if(at_least_one_slot == True and len(ar_rows) > 0):
					query   = f"replace into bot_cnv_config (cnv_id,date_sent,var_name,var_value) values (%s,now(),%s,%s)"
					_db.insert_many(query, ar_rows)
						
				break
		
		# Get or create the conversation
		_cnv.get_or_create()

		# At the end, add an `action_listen` to continue listening the user
		# events.append(ActionExecuted("action_listen"))

		_logger.info("Executed: set_variables()")

		return events
		#return []

'''
This class saves the response usefulness stated by the user 
when asked 'Did that help?' 
'''
class log_response_usefulness(Action):
	
	'''
	Returns the name of the action. Required by RASA
	'''
	def name (self) -> Text:
		return "log_response_usefulness"
	
	'''
	Executes the custom code for this action.
	'''
	async def run (    
		self,
		_dispatcher : CollectingDispatcher,
		_tracker : Tracker,
		_domain : Dict[Text, Any],
	) -> List[Dict[Text, Any]]:

		_rpl 	= rpl.replies_handler(_logger,_tracker,_db)

		_rpl.log_usefulness()

		return []

'''
This class returns a json message with a request cnv.redirect
in order to allow the user to chat wit a school staff 
'''
class chat_with_school_staff(Action):
	
	'''
	Returns the name of the action. Required by RASA
	'''
	def name (self) -> Text:
		return "chat_with_school_staff"
	
	'''
	Executes the custom code for this action.
	'''
	async def run (    
		self,
		_dispatcher : CollectingDispatcher,
		_tracker : Tracker,
		_domain : Dict[Text, Any],
	) -> List[Dict[Text, Any]]:
		
		_cnv            = cnv.conversations_handler(_logger,_tracker,_db)
		_ans 			= ans.answers_handler(_logger,_tracker,_domain,_db)

		school_user_in_charge   = None
		prv_user_first_name     = 'Este usuario'

		# Get the support assistant from the bot conversation vars (configuration vars).
		slots = _tracker.slots

		if(
			"config.technical_support.school_user_in_charge" in slots
			and slots["config.technical_support.school_user_in_charge"] is not None
		):
			school_user_in_charge = slots["config.technical_support.school_user_in_charge"]
		
		if(
			"user.first_name" in slots
			and slots["user.first_name"] is not None
		):
			prv_user_first_name = slots["user.first_name"]

		# Get conversation history
		cnv_history = _cnv.get_history()

		# Create a custom json with a callback action to create 
		# a new conversation with the school support assistant.
		try:
			if(school_user_in_charge is not None and cnv_history is not None):
				# Send a message to the user informing conversation being sent to school staff.
				msg = _ans.get_one_expression("utter_i_will_send_this_conversation_to_school_staff")

				# Send the json message to the PMS and user in charge
				msg_to_new_user = _ans.get_one_expression("utter_hello_school_staff_i_was_asked_to_transfer_conversation")

				msg_to_new_user = msg_to_new_user.format(prv_user_first_name = prv_user_first_name)

				json_msg = {
					"success"         : True,
					"data"            : {
						"text"            : msg,
						"cnv_history"     : cnv_history,
						"callback"        : {
							"action" : "cnv.redirect",
							"params" : {
								"msg_to_new_user" 	: msg_to_new_user,
								"redirect_to" 		: school_user_in_charge
							}
						}
					}
				}
				
				_dispatcher.utter_message(json_message=json_msg)

			else:
				# No school user in charge of attending others. Inform the user
				msg = _ans.get_one_expression("utter_wa_there_is_no_school_support_user_defined") + "\n"
				msg += _ans.get_one_expression("utter_please_contact_the_school")
				_dispatcher.utter_message(text=msg)
			
		except:
			_logger.warning("The custom json msg could not be sent")

		return []

'''
This class sends a copy of the current conversation 
to a school staff defined in CE configuration vars  
'''
class email_school_staff(Action):
	
	'''
	Returns the name of the action. Required by RASA
	'''
	def name (self) -> Text:
		return "email_school_staff"
	
	'''
	Executes the custom code for this action.
	'''
	async def run (    
		self,
		_dispatcher : CollectingDispatcher,
		_tracker : Tracker,
		_domain : Dict[Text, Any],
	) -> List[Dict[Text, Any]]:

		_cnv            = cnv.conversations_handler(_logger,_tracker,_db)
		_ans 			= ans.answers_handler(_logger,_tracker,_domain,_db)
		slots           = _tracker.slots
		recipient_email = ''

		# Get the school's support email from the bot conversation
		# vars (configuration vars) and send the email
		if(
			"config.technical_support.school_email" in slots
			and slots["config.technical_support.school_email"] is not None
		):
			recipient_email = slots["config.technical_support.school_email"]
			params          = {
				"recipient_email" : recipient_email
			}
			
			_cnv.send_to_email(params)

			# Inform the user, that the message was sent
			msg = _ans.get_one_expression("utter_i_have_sent_a_copy_of_the_conversation_to")
			msg = msg.format(recipient_email=recipient_email)
			
			_dispatcher.utter_message(text=msg)

		else:
			# Inform the user, that the message could not be sent
			msg = _ans.get_one_expression("utter_wa_there_is_no_school_support_email_defined")
			msg += _ans.get_one_expression("utter_please_contact_the_school")

			_dispatcher.utter_message(text=msg)

		return []

'''
This class sends a copy of the current conversation 
to a support assistant defined in CE configuration vars  
'''
class email_support_assistant(Action):
	
	'''
	Returns the name of the action. Required by RASA
	'''
	def name (self) -> Text:
		return "email_support_assistant"
	
	'''
	Executes the custom code for this action.
	'''
	async def run (    
		self,
		_dispatcher : CollectingDispatcher,
		_tracker : Tracker,
		_domain : Dict[Text, Any],
	) -> List[Dict[Text, Any]]:

		_cnv            = cnv.conversations_handler(_logger,_tracker,_db)
		_ans 			= ans.answers_handler(_logger,_tracker,_domain,_db)

		recipient_email = 'soporte@ciudadeducativa.com'        
		params          = {
			"recipient_email" : recipient_email
		}

		_cnv.send_to_email(params)

		# Inform the user, that the message was sent
		msg = _ans.get_one_expression("utter_i_have_sent_a_copy_of_the_conversation_to")
		msg = msg.format(recipient_email=recipient_email) 
		
		_dispatcher.utter_message(text=msg)

		return []

'''
This class returns a copy of the conversation in a json format
'''
class get_conversation_history(Action):
	
	'''
	Returns the name of the action. Required by RASA
	'''
	def name (self) -> Text:
		return "get_conversation_history"
	
	'''
	Executes the custom code for this action.
	'''
	async def run (    
		self,
		_dispatcher : CollectingDispatcher,
		_tracker : Tracker,
		_domain : Dict[Text, Any],
	) -> List[Dict[Text, Any]]:

		_cnv            = cnv.conversations_handler(_logger,_tracker,_db)
		cnv_history     = _cnv.get_history()

		json_msg = {
			"success"         : True,
			"data"            : {
				"cnv_history"     : cnv_history,
			}
		}
		
		_dispatcher.utter_message(json_message=json_msg)

		return []

'''
This class checks an utterance identified as FAQ and tries to identify the specific FAQ to answer to.
If the confidence is very low, it shows the user a list with the highest confidence intents after 
receiving an utterance that the bot can not identify.
The highest confidence intents would not have 'high' confidence indeed.
'''
class analyze_user_expression(Action):
	
	'''
	Returns the name of the action. Required by RASA
	'''
	def name (self) -> Text:
		return "analyze_user_expression"
	
	'''
	Executes the custom code for this action.
	'''
	async def run (    
		self,
		_dispatcher : CollectingDispatcher,
		_tracker : Tracker,
		_domain : Dict[Text, Any],
	) -> List[Dict[Text, Any]]:

		_ans 				= ans.answers_handler(_logger,_tracker,_domain,_db)
		_int 				= int.intents_handler(_logger,_tracker,_domain,_db)

		error 				= False
		events 				= []
		ar_option_buttons 	= []
		lm 					= _tracker.latest_message
		rs_ranking 			= lm["intent_ranking"]
		group_type 			= 'faq'
		ir_mpi 				= rs_ranking[0] 

		_logger.info('analyze_user_expression: ' + lm['text'])
		_logger.info(ir_mpi)
		
		events.append(SlotSet(key="cnv.one_faq_received", value="1"))
		
		if(ir_mpi["name"] in ["faq","chitchat"]):
			group_type 		= ir_mpi["name"]
		else:
			if(ir_mpi["confidence"] > 0.5):
				_logger.warning(
					"\nintent_ranking mpi has probability over 0.5 and is not faq nor chitchat."
					"\nMaybe utterance was blocked by rules."
				)
				_dispatcher.utter_message(text = "😳...")

				error = True

		if(error == False):
			#Get the most probable intent
			mpi 				= _int.get_most_probable_intent()
			mp_intent 			= mpi["mp_intent"]
			ar_option_buttons 	= mpi["ar_option_buttons"]

			_logger.info('mpi')
			_logger.info(mpi)

			# If one intent was identified, check if there is only one answer or several answers,
			# and one of those has specific matching conditions
			if(mp_intent is not None):

				intent_parts 	= mp_intent["intent_response_key"].strip().split("/")
				group_type 		= intent_parts[0]

				# Select the best answer for this intention
				seld_answer 	= _ans.get_best_answer(mp_intent)
				
				# If the answer is of type text, send it as text
				if("text" in seld_answer): 
					_dispatcher.utter_message(text = seld_answer['text'])
				
				# If the body of the selected answer is 'custom' send it in json format
				elif("custom" in seld_answer): # Custom answer.
					_dispatcher.utter_message(json_message = seld_answer['custom'])

				# If the intent group type is FAQ and one good answer was identified, ask if the answer was helpful
				if(
					"no_answer" not in seld_answer
					and group_type == 'faq'
				):
					_dispatcher.utter_message(response = "utter_did_that_help")
					events.append(ActionExecuted("utter_did_that_help"))

			# If no intent was identified
			else:
				# Respond to the user

				if(group_type == 'faq'):
					if(len(ar_option_buttons) > 0):
						_dispatcher.utter_message(response 	= "utter_i_found_similar_questions")
						_dispatcher.utter_message(buttons 	= ar_option_buttons)
						_dispatcher.utter_message(response 	= "utter_if_none_of_these_questions_then_rephrase")
						useful = 'similar-questions-found'
					else:
						_dispatcher.utter_message(response = "utter_please_rephrase")
						useful = 'not-understood'
				else:
					_dispatcher.utter_message(response = "utter_please_rephrase")
					useful = 'not-understood'
				
				# Store the response usefulness

				_rpl 	= rpl.replies_handler(_logger,_tracker,_db)

				_rpl.log_usefulness(question = lm['text'], useful = useful)
		
		return events