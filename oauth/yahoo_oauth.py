import config
import base64
import requests
from app import *
import models.status
from .web_token import *

def get_access_token(client_id, client_secret, redirect_uri, code):
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
	return response

def refresh_access_token(client_id, client_secret, redirect_uri):
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
		return True
	else:
		print("Error getting token. ")
		print("HTTP Code: %s" % response.status_code)
		print("HTTP Response: \n%s" % response.content)
		return False

def oauth_login(code):
  if code == '' or code is None:
    return jsonify(
      {
        'success': False,
        'error': 'No code provided',
        'status': 400
      }
    )
  response = get_access_token(config.client_id, config.client_secret, config.redirect_uri, code)
  if response.status_code >= 200 and response.status_code <= 203:
    token_response=response.json()

    session['access_token'] = token_response['access_token']
    session['refresh_token'] = token_response['refresh_token']
    teams, my_team = models.status.set_team_sessions()
    web_token = generate_web_token(my_team, token_response['access_token'], token_response['refresh_token'])
    print(f"\n\nNEW LOGIN: {my_team}\n\n")

    return jsonify({
        'success': True,
        'pub': config.pubnub_publish_key, 
        'sub': config.pubnub_subscribe_key,
        'user': my_team,
        'teams': teams,
        'web_token': web_token
      })
  else:
    print(f"Login error. {response}.")
    print(f"Response: {response.status_code}. Error: {response.text}.")
    return jsonify({
        'success': False,
        'error': str(response),
        'status': response.status_code
      })

def oauth_logout():
  try:
	  session.clear()
	  return jsonify({'success': True})
  except Exception(e):
    error = 'Error clearing session: ' + str(e)
    return jsonify({'success': False, 'error': error})
