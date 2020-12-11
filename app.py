from flask import Flask, request, send_from_directory, session, request, url_for, redirect, render_template, jsonify, flash, send_from_directory
from oauth import *
from random import randint
import time
import config
import os, sys, json

app = Flask(__name__, 
  static_url_path='',
  static_folder='build',
  template_folder='build')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
  if path != "" and os.path.exists(app.static_folder + '/' + path):
    return send_from_directory(app.static_folder, path)
  else:
    return send_from_directory(app.static_folder, 'index.html')

# @app.route('/oauth_data', methods=['GET'])
# def oauth_data():
#   code = request.args.get('code', default='')
#   if code != '':
#     return redirect(url_for('login'))
#   session['state'] = str(randint(1000000, 99999999))
#   oauth_data = {
#     "client_id": config.client_id,
#     "redirect_uri": config.redirect_uri,
#     "state": session['state']
#   }
#   return jsonify(oauth_data)

@app.route('/check_login')
def check_login():
  if 'access_token' in session and 'refresh_token' in session:
    return jsonify({'success': True, 'pub': config.pubnub_publish_key, 'sub': config.pubnub_subscribe_key})
  return jsonify({'success': False, 'error': 'Unable to get access token'})

@app.route('/logout')
def logout():
  try:
	  session.clear()
	  return jsonify({'success': True})
  except Exception(e):
    error = 'Error clearing session: ' + str(e)
    return jsonify({'success': False, 'error': 'Unable to clear session'})


@app.route('/login/<string:code>', methods=['GET'])
def login(code):
  # if 'access_token' in session:
  #   print("Success!\n\n")
  #   print(session['access_token'])
  #   return {"access_token": session["access_token"]}
  if code != '':
    # if 'yahoo' in session:
    #   return jsonify({'response': 'Already logged in.'})
    response = get_access_token(config.client_id, config.client_secret, config.redirect_uri, code)
    if response == True:
      return jsonify(
        {
          'response': 'success',
          'access_token': session['access_token'],
          'refresh_token': session['refresh_token']
        }
      ) 
    else:
      return jsonify(
        {
          'response': 'error',
          'message': response
        }
      ) 
      
  else:
    print('Warning: No code provided.')
    return jsonify({'response': 'No code provided'}) 


@app.route('/test')
def time():
  response = {'test': 'test worked'}
  return jsonify(response)

if __name__== '__main__':
  import credentials
  app.secret_key = credentials.SECRET_KEY

  # get Yahoo Oauth credentials
  config.client_id = credentials.consumer_key
  config.client_secret = credentials.consumer_secret
  config.redirect_uri = "oob"
  config.pubnub_publish_key = credentials.pubnub_publish_key
  config.pubnub_subscribe_key = credentials.pubnub_subscribe_key
  app.run(use_reloader=True, port=5000, threaded=True, debug=True)
else:
  if 'flask_secret_key' in os.environ:
    app.secret_key = os.environ['flask_secret_key']
  
  if 'client_id' in os.environ:
    config.client_id = os.environ['client_id']
    config.client_secret = os.environ['client_secret']
    config.redirect_uri = "https:///slowdraft.herokuapp.com"
  if 'pub' in os.environ:
    config.pubnub_publish_key = os.environ['pubnub_publish_key']
    config.pubnub_subscribe_key = os.environ['pubnub_subscribe_key']

  # app.secret_key = os.environ['flask_secret_key']
  @app.before_request
  def force_https():
    if request.endpoint in app.view_functions and not request.is_secure:
      return redirect(request.url.replace('http://', 'https://'))
