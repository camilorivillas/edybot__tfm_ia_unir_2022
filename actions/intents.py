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
import random

'''
This class handles all the logic related to the intents
'''
class intents_handler():
	
	'''
	Class constructor
	'''
	def __init__(
		self,
		_logger,
		_tracker,
		_domain,
		_db,
	):
		self._logger    = _logger
		self._tracker   = _tracker
		self._domain   	= _domain
		self._db        = _db

		self.limits = {
			"faq" : {
				'sure' 	: 0.40,
				'high' 	: 0.20,
				'min' 	: 0.10,
				'diff' 	: 0.07
			},
			"chitchat" : {
				'sure' 	: 0.50,
				'high' 	: 0.40,
				'min' 	: 0.30,
				'diff' 	: 0.25
			}
		}
	
	'''
	Returns one intent from the database
	'''
	def get_from_db(
		self,
		int_id,
	) -> List[Dict[Text, Any]]:

		intent 	= self._db.select_many(f"select * from bot_intentions where int_id = %s",(int_id,))
		return intent
	
	'''
	Returns several intents from the database
	'''
	def get_many_from_db(
		self,
		int_id,
	) -> List[Dict[Text, Any]]:

		ar_intents = self._db.select_many("select *, int_id as row_id from bot_intentions where int_id in ("+int_id+")",(),'int_id')
		return ar_intents
	
	'''
	Returns one intent from the domain.yml file
	'''
	def get_from_domain(
		self,
		int_id,
	) -> List[Dict[Text, Any]]:

		int_code = str(int_id).zfill(4)

		for intent in self._domain["intents"]:
			if(
				"__int_" in intent 
				and "/" in intent 
				and int_code in intent
			):
				ar_intents = self._domain["intents"][intent]

		return ar_intents

	'''
	Returns one expression (text) from the list of expression of a given intent
	'''
	def get_one_expression(
		self,
		intent_name,
	) -> Text:

		msg 		= ''
		ar_intents 	= self._domain["intents"][intent_name]
		r 			= random.randint(1,len(ar_intents)) - 1
		intent 		= ar_intents[r]

		if("text" in intent):
			msg = intent['text']

		return msg
	
	'''
	Returns the most probable intent according to the latest_message in the tracker
	'''
	def get_most_probable_intent(
		self,
	) -> Dict[Text, Any]:
		mp_intent 			= None
		first_guess 		= None
		second_guess 		= None
		ar_intent_ids 		= []
		ar_option_buttons 	= []
		qt_ints_detected 	= 0
		confidence_diff 	= 0

		retrieval_intent 	= 'default'
		lm 					= self._tracker.latest_message
		rs_ranking 			= lm["intent_ranking"]
		ir_mpi 				= rs_ranking[0]	
		int_ranking 		= lm["response_selector"][retrieval_intent]["ranking"]
		ar_best_options 	= int_ranking[0:5] # {confidence, intent_response_key} # "faq/lms__class_material__int_0110"

		group_type 			= 'faq'
		group_confidence 	= 0

		if(ir_mpi["name"] in ["faq","chitchat"]):
			group_type 		= ir_mpi["name"]
			group_confidence= ir_mpi["confidence"]
		
		limits = self.limits[group_type]

		# Get the intents and its details from the database core_support.bot_intentions

		for option in ar_best_options:
			intent_rk 		= option["intent_response_key"]
			
			if(
				"__int_" in intent_rk 
				and (group_type + "/" in intent_rk)
			):
				try:
					int_id = int(intent_rk[::-1][0:4][::-1])
					ar_intent_ids.append(str(int(int_id)))
				except:
					int_id = 'not-found'

		if(len(ar_intent_ids) > 0):
			str_intent_ids 	= ','.join(ar_intent_ids)
			ar_intents 		= self.get_many_from_db(str_intent_ids)
		
		# Check the confidence of the best options
		for option in ar_best_options:
			intent_rk 		= option["intent_response_key"]
			confidence 		= option["confidence"]

			try:
				int_id = int(intent_rk[::-1][0:4][::-1])
			except:
				int_id = 'not-found'

			if(
				"__int_" in intent_rk 
				and ("faq/" in intent_rk or "chitchat/" in intent_rk)
				and int_id in ar_intents
				and "text" in ar_intents[int_id]
			):
				option["int_id"] 	= int_id
				qt_ints_detected 	+= 1
				
				# If confidence is over limits[sure], we can assume this is the correct option. 
				# There is no need to further check
				if(first_guess is None):

					first_guess 	= dict(option)

					if(confidence > limits["sure"]):
						mp_intent = first_guess.copy()
						break
				
				elif(second_guess is None):
					second_guess 	= dict(option)
					confidence_diff = first_guess["confidence"] - second_guess["confidence"]

					if(
						first_guess["confidence"] > limits["high"]
						and
						confidence_diff > limits["diff"]
					):
						mp_intent = first_guess.copy()
						break

				# check highest-confidence options and add those with confidence > limits[min] as a button
				if(
					confidence > limits["min"]
					and 
					"faq/" in intent_rk
				):
					ar_option_buttons.append({
						'title' 	: ar_intents[int_id]["text"], 
						'payload' 	: '/' + intent_rk, 
					})
		return {
			"mp_intent" 		: mp_intent,
			"ar_option_buttons" : ar_option_buttons,
		}