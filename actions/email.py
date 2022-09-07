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
import requests
from requests.structures import CaseInsensitiveDict
import os
import json
from dotenv import load_dotenv
load_dotenv()
import pycurl
from io import BytesIO

'''
This class handles connection to MySQL database
'''
class email_handler():
	
	'''
	Class constructor
	'''
	def __init__(
		self,
		_logger,
	):
		self._logger    = _logger

	'''
	Sends an email using curl
	'''
	def send_with_curl(
		self,
		params = ()    
	):

		E_EXTERNAL_URL_EMAIL 		= str(os.getenv('E_EXTERNAL_URL_EMAIL'))
		E_URL_EMAIL 				= str(os.getenv('E_URL_EMAIL'))
		E_AUTHORIZATION 			= str(os.getenv('E_AUTHORIZATION'))
		E_EXTERNAL_AUTHORIZATION 	= str(os.getenv('E_EXTERNAL_AUTHORIZATION'))
		E_NOTIFICATION_EMAIL 		= str(os.getenv('E_NOTIFICATION_EMAIL'))

		email_from 		= E_NOTIFICATION_EMAIL
		email_reply_to 	= E_NOTIFICATION_EMAIL
		name_from 		= "Ciudad Educativa"

		if(
			params is not None
			and
			"subject" in params
			and
			"body" in params
			and
			"recipients" in params
		):
			subject 			= params["subject"]
			body 				= params["body"]
			recipients 			= params["recipients"]

			if(
				"email_from" in params 
				and
				len(params["email_from"]) > 8
				and
				"@" in params["email_from"]
			):
				email_from 		= params["email_from"]
				email_reply_to 	= params["email_from"]
			
			if("name_from" in params):
				name_from 		= params["name_from"]

			email_from 		= E_NOTIFICATION_EMAIL
			email_reply_to 	= E_NOTIFICATION_EMAIL
			name_from 		= "Ciudad Educativa"
			
			# Set params for CURL
			crl 			= pycurl.Curl() 

			# Set URL value
			url 			= E_EXTERNAL_URL_EMAIL

			headers = [
				'Content-Type: ' + 'application/json'
				'Access-Control-Request-Method: ' + 'application/json',
				'Accept: application/json',
				'Authorization: ' + E_EXTERNAL_AUTHORIZATION
			]

			payload = {
				"masivianUrl" 	: E_URL_EMAIL,
				"authorization" : E_AUTHORIZATION,
				"masivianData" 	: {
					"Subject" 	: subject,
					"From" 		: name_from + "<" + email_from + ">",
					"Template" 	: {
						"Type" 	: "text/html",
						"Value" : body
					},
					"ReplyTo"		: email_reply_to,
					"Recipients"	: recipients
				}
			}

			json_payload 	= json.dumps(payload)

			crl.setopt(pycurl.URL, url)
			crl.setopt(pycurl.CUSTOMREQUEST, 'POST')
			crl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1) # Other versions available, HTTP 1.1 is the most common.
			crl.setopt(pycurl.FOLLOWLOCATION, True)				# Allow header Location to change
			crl.setopt(pycurl.POST, True) 						# 1,0. 1: Perform a default POST request
			crl.setopt(pycurl.TIMEOUT, 0) 						# 0: Never time out
			crl.setopt(pycurl.MAXREDIRS, 10) 					# 10 max redirections
			crl.setopt(pycurl.POSTFIELDS, json_payload)			# The request itself
			crl.setopt(pycurl.HEADER, False)					# Do not set a manual? Header ?????
			crl.setopt(pycurl.HTTPHEADER, headers)				# Custom headers
			crl.setopt(pycurl.SSL_VERIFYPEER, False)			# Do not verify SSL in destination

			# Perform the request
			result = crl.perform() 

			# Close the curl connector
			crl.close()

		return []

	'''
	Sends an email using a request object
	'''
	def send(
		self,
		params = ()    
	):
		
		E_EXTERNAL_URL_EMAIL 		= str(os.getenv('E_EXTERNAL_URL_EMAIL'))
		E_URL_EMAIL 				= str(os.getenv('E_URL_EMAIL'))
		E_AUTHORIZATION 			= str(os.getenv('E_AUTHORIZATION'))
		E_EXTERNAL_AUTHORIZATION 	= str(os.getenv('E_EXTERNAL_AUTHORIZATION'))
		E_NOTIFICATION_EMAIL 		= str(os.getenv('E_NOTIFICATION_EMAIL'))

		email_from 		= E_NOTIFICATION_EMAIL
		email_reply_to 	= E_NOTIFICATION_EMAIL
		name_from 		= "Ciudad Educativa"
		recipients 		= []

		if(
			params is not None
			and
			"subject" in params
			and
			"body" in params
			and
			"recipients" in params
		):
			subject 			= params["subject"]
			body 				= params["body"]

			recipients.append({"To":params["recipients"]})

			if(
				"email_from" in params 
				and
				len(params["email_from"]) > 8
				and
				"@" in params["email_from"]
			):
				email_from 		= params["email_from"]
				email_reply_to 	= params["email_from"]
			
			if("name_from" in params):
				name_from 		= params["name_from"]

			email_from 		= E_NOTIFICATION_EMAIL
			email_reply_to 	= E_NOTIFICATION_EMAIL
			name_from 		= "Ciudad Educativa"
			
			# Set URL value
			url 			= E_EXTERNAL_URL_EMAIL

			payload 		= {
				"masivianUrl" 	: E_URL_EMAIL,
				"authorization" : E_AUTHORIZATION,
				"masivianData" 	: {
					"Subject" 	: subject,
					"From" 		: name_from + "<" + email_from + ">",
					"Template" 	: {
						"Type" 	: "text/html",
						"Value" : body
					},
					"ReplyTo"		: email_reply_to,
					"Recipients"	: recipients
				}
			}

			json_payload 	= json.dumps(payload)

			headers = CaseInsensitiveDict()

			headers["Access-Control-Request-Method"] 	= 'application/json'
			headers["Accept"] 							= 'application/json'
			headers["Authorization"] 					= E_EXTERNAL_AUTHORIZATION
			headers["Access-Control-Request-Headers"] 	= E_EXTERNAL_AUTHORIZATION

			resp = requests.post(url, headers=headers, json=payload)
