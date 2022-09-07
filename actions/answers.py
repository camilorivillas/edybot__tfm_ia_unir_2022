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
import actions.conditions as cnd
import io
import yaml

'''
This class handles all the logic regarding the answers
'''
class answers_handler():
	
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
	
	'''
	Returns the relevant conversation history data from the _tracker
	'''
	def get_from_db(
		self,
		int_id,
	) -> List[Dict[Text, Any]]:

		ar_answers 	= self._db.select_many(f"select * from bot_answers where int_id = %s",(int_id,))
		return ar_answers

	'''
	Returns the relevant conversation history data from the _tracker
	'''
	def get_from_domain_extended(
		self,
		int_id,
	) -> List[Dict[Text, Any]]:
		ar_answers 	= []
		with open(r'domain_extended.yml') as file:
			de = yaml.load(file, Loader=yaml.FullLoader)
			ar_responses = de["responses"]
		
		file.close()

		int_code 	= str(int_id).zfill(4)

		for response in ar_responses:
			if(
				"__int_" in response 
				and "/" in response 
				and int_code in response
			):
				ar_answers = ar_responses[response]

		return ar_answers
	
	'''
	Returns the relevant conversation history data from the _tracker
	'''
	def get_from_domain(
		self,
		int_id,
	) -> List[Dict[Text, Any]]:
		ar_answers 		= []
		ar_responses 	= self._domain["responses"]
		int_code 		= str(int_id).zfill(4)

		for response in ar_responses:
			if(
				"__int_" in response 
				and "/" in response 
				and int_code in response
			):
				ar_answers = ar_responses[response]

		return ar_answers

	'''
	Returns one random expression from the list of possible answers for a given utterance
	'''
	def get_one_expression(
		self,
		utter_action,
	) -> Text:

		msg 		= ''
		ar_answers 	= self._domain["responses"][utter_action]
		r 			= random.randint(1,len(ar_answers)) - 1
		answer 		= ar_answers[r]

		if("text" in answer):
			msg = answer['text']

		return msg

	'''
	Returns the best matching answer for a specific intent
	'''
	def get_best_answer(
		self,
		mp_intent
	) -> Dict[Text, Any]:

		_cnd 			= cnd.conditions_handler(self._logger,self._tracker)
		int_id 			= mp_intent["int_id"]

		ar_answers 		= self.get_from_domain_extended(int_id)

		ncnd_answer 	= None # Not conditioned answer
		cond_answer 	= None # Conditioned answer
		seld_answer 	= None # Selected answer

		there_are_conds = False

		for answer in ar_answers:
			# If conditions are present
			if("condition" in answer or "conditions" in answer):
				there_are_conds = True
				break


		# There is only one answer
		if(len(ar_answers) == 1):
			seld_answer = ar_answers[0]

		# If there is more than one answer, and none of them has conditions
		elif(len(ar_answers) > 1 and there_are_conds == False):
			seld_answer = random.choice(ar_answers)
			
		# If there is more than one answer, and at least one of them has conditions
		elif(len(ar_answers) > 1 and there_are_conds == True):
			for answer in ar_answers:
				# If conditions are present
				if("condition" in answer): # Domain syntax
					# Check which one fulfills the conditions
					match = _cnd.match(answer["condition"])

					if(match == True):
						cond_answer = answer
						break
				elif("conditions" in answer): # Table core_support.bot_answers syntax
					# Check which one fulfills the conditions
					match = _cnd.match(answer["conditions"])

					if(match == True):
						cond_answer = answer
						break
				
				# If no conditions are present
				else:
					ncnd_answer = answer

			if(cond_answer is not None):
				seld_answer = cond_answer
			
			elif(ncnd_answer is not None):
				seld_answer = ncnd_answer

		# There is no answer
		else:
			seld_answer = {"text" : self.get_one_expression("utter_out_of_scope"), "no_answer": True}
			
		# Return the selected answer
		return seld_answer
