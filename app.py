from flask import Flask, session, request, url_for, redirect, render_template, jsonify, flash, send_from_directory
from oauth.oauth import *
from random import randint

import config

app = Flask(__name__)

@app.route('/login', methods=['GET'])
def index():
  session['state'] = str(randint(1000000, 99999999))
  response, success = getAccessToken(config.client_id, config.client_secret, config.redirect_uri, code)
  test()
  return "Hello world"

if __name__== '__main__':
  import credentials
  app.secret_key = credentials.SECRET_KEY

  # get Yahoo Oauth credentials
  config.client_id = credentials.consumer_key
  config.client_secret = credentials.consumer_secret
  config.redirect_uri = "oob"
  app.run(debug=True)
