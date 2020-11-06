import config
import base64
import requests
# from yahoo_api import *
# from models import draft
# import db

# YAHOO_AUTH_URL = 'https://api.login.yahoo.com/oauth2/request_auth?client_id=' + config.client_id + \
# 				"&redirect_uri=" + config.redirect_uri + "&response_type=code&language=en-us&state=" + str(session['state'])	

def test():
  print("test")

def getAccessToken(client_id, client_secret, redirect_uri, code):
	# This function takes the 7 digit code from the user and attempts to get a yahoo access token 
	# If successful, the access and refresh tokens that are returned will be stored as session variables
	base64_token = base64.b64encode((client_id + ':' + client_secret).encode())
	token = base64_token.decode("utf-8")
	headers = {
		'Content-Type': 'application/x-www-form-urlencoded',
		'Authorization': 'Basic ' + str(token),
	}	
	data = {
		'grant_type': 'authorization_code',
		'code': str(code),
		'client_id': client_id,
		'client_secret': client_secret,
		'redirect_uri': str(redirect_uri)
	}
	response = requests.post(config.GET_TOKEN_URL, headers=headers, data=data)
	print("\nResponse: " + str(response))
	print(str(response.json()))
	if response.status_code >= 200 and response.status_code <= 203:
		token_response=response.json()
		session['yahoo'] = True
		session['access_token'] = token_response['access_token']
		session['refresh_token'] = token_response['refresh_token']
		session['guid'] = token_response['xoauth_yahoo_guid']
		return '', True
	else:
		return response.json(), False

def refreshAccessToken(client_id, client_secret, redirect_uri):
	# Oauth access tokens expire after one hour
	# If it is expired, this function uses the refresh token stored in the session to get a new one
	print("Refreshing access token...")
	data = {
		'client_id' : client_id,
		'client_secret' : client_secret,
		'redirect_uri' : redirect_uri, 
		'refresh_token' : session['refresh_token'], 
		'grant_type' : 'refresh_token'
	}
	response = requests.post(config.GET_TOKEN_URL, data)
	if response.status_code >= 200 and response.status_code <= 203:
		token_response = response.json()
		session['yahoo'] = True
		session['access_token'] = token_response['access_token']
		session['refresh_token'] = token_response['refresh_token']
		session['guid'] = token_response['xoauth_yahoo_guid']
		return True
	else:
		print("Error getting token. ")
		print("HTTP Code: %s" % response.status_code)
		print("HTTP Response: \n%s" % response.content)
		return False
