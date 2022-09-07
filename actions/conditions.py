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

'''
This class handles all the logic regarding the conditions
'''
class conditions_handler():
	'''
	Class constructor
	'''
	def __init__(
		self,
		_logger,
		_tracker,
	):
		self._logger  	= _logger
		self._tracker  	= _tracker
	
	'''
	Parses a conditions text from the database and turns it into a list of condition objects
	'''
	def parse(
		str_conditions
	) -> List[Dict[Text, Any]]:
		ar_conditions = []

		if(
			str_conditions is not None 
			and 
			str_conditions is not null
		):
			ar_lines = str_conditions.strip().split('|')
			for line in ar_lines:
				if(":" in line):
					ar_parts = line.strip().split(":")

					if(len(ar_parts) >= 3):
						new_condition = {
							"name" 				: ar_parts[0],
							"logical_operator" 	: ar_parts[1],
						}
						
						if(2 in ar_parts):
							new_condition["value"] = ar_parts[2]
						
						ar_conditions.append(new_condition)

		return ar_conditions

	'''
	Receives a conditions string or list of conditions object and checks if these conditions match the slots in the tracker
	'''		
	def match(
		self,
		conditions
	) -> bool:
		
		match = True

		if(type(conditions) == str): # This is a string of conditions obtained from database
			ar_conditions = self.parse(conditions)

		elif(type(conditions) == list): # This is a list of conditions obtained from rasa domain.yml file
			ar_conditions = conditions

		for condition in ar_conditions:

			#print(condition)

			var_name 				= condition["name"]
			var_logical_operator 	= 'equal_to'
			
			if ("logical_operator" in condition):
				var_logical_operator 	= condition["logical_operator"]
			
			var_value 				= ''

			if("value" in condition):
				var_value = condition["value"]

			if(var_name not in self._tracker.slots):
				match = False
			else:
				slot_value = self._tracker.slots[var_name]

				if(
					var_logical_operator == 'is_defined'
					and
					slot_value is None
				):
					match = False

				elif(
					(var_logical_operator == '>' or var_logical_operator == 'greater_than')
					and slot_value is not None
					and float(slot_value) <= float(var_value)
				):
					match = False

				elif(
					(var_logical_operator == '<' or var_logical_operator == 'lesser_than')
					and slot_value is not None
					and float(slot_value) >= float(var_value)
				):
					match = False

				elif(
					(var_logical_operator == '>=' or var_logical_operator == 'greater_than_or_equal_to')
					and slot_value is not None
					and float(slot_value) < float(var_value)
				):
					match = False
				
				elif(
					(var_logical_operator == '<=' or var_logical_operator == 'lesser_than_or_equal_to')
					and slot_value is not None
					and float(slot_value) > float(var_value)
				):
					match = False

				elif(
					(var_logical_operator == '!=' or var_logical_operator == 'different_from')
					and slot_value is not None
					and slot_value == var_value
				):
					match = False
				
				elif(
					(var_logical_operator == '==' or var_logical_operator == 'equal_to')
					and slot_value is not None
					and slot_value != var_value
				):
					match = False
		
		return match

