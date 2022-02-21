from flask import Flask, request, send_from_directory, session, request, \
  url_for, redirect, render_template, jsonify, flash, send_from_directory
from oauth import *
from oauth.web_token import *
from random import randint
import time
import config
import os, sys, json
import xmltodict
from models.league import *
from models.players import *
from models.forum import *
from models.status import *
from models.draft import *
from models.team import *
from models.rules import *
from models.emails import *
from yahoo_api import *
import db
import datetime
import pymysql

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

@app.route('/logout', methods=['GET'])
def logout():
  return oauth_logout()

@app.route('/login/<string:code>', methods=['GET'])
def login(code):
  return oauth_login(code)

@app.route('/check_for_updates', methods=['GET'])
@exception_handler
def check_for_updates_with_user_and_league(user):
  print(f"Getting updates for {user['team_name']} ({user['team_key']})")
  return get_updates_with_league(user['yahoo_league_id'], user['team_key'])

@app.route('/get_db_players', methods=['GET'])
@exception_handler
def get_players_from_db(user):
  position = request.args.get('position', default='skaters')
  return get_db_players(user['draft_id'], position)

@app.route('/get_teams')
@exception_handler
def get_teams(user):
  return get_teams_from_db(user['draft_id'])

# -------------------------- Forum & Rules routes --------------------------

@app.route('/get_forum_posts', methods=['GET'])
@exception_handler
def forum(user):
  return get_forum_posts(user['yahoo_league_id'])

@app.route('/new_forum_post', methods=['POST'])
@exception_handler
def post_to_forum(user):
  post = json.loads(request.data)
  return new_forum_post(post, user)

@app.route('/update_forum_post', methods=['POST'])
@exception_handler
def update_post(user):
  post = json.loads(request.data)
  return update_forum_post(user, post['title'], post['body'], post['id'], post['parent_id'])

@app.route('/view_post_replies/<int:post_id>', methods=['GET'])
@exception_handler
def view_forum_post_replies(user, post_id):
  return get_post_replies(user['yahoo_league_id'], post_id)

@app.route('/get_all_rules', methods=['GET'])
@exception_handler
def get_all_rules(user):
  return get_rules(user['yahoo_league_id'])

@app.route('/create_rule', methods=['POST'])
@exception_handler
@check_if_admin
def create_rule(user):
  post = json.loads(request.data)
  return new_rule(post, user)

@app.route('/edit_rule', methods=['POST'])
@exception_handler
@check_if_admin
def edit_rule(user):
  post = json.loads(request.data)
  return update_rule(post, user)

# -------------------------- Draft routes --------------------------

@app.route('/get_draft', methods=['GET'])
@exception_handler
def get_dps(user):
  return get_draft(user['draft_id'], user['team_key'])

@app.route('/draft/<int:player_id>', methods=['GET'])
@exception_handler
def draft_player(user, player_id):
  return make_pick(user['draft_id'], player_id, user['team_key'])

# -------------------------- Admin routes --------------------------

@app.route('/make_pick', methods=['POST'])
@exception_handler
@check_if_admin
def draft_player_admin(user):
  post = json.loads(request.data)
  return make_pick(user['draft_id'], post['player_id'], post['team_key'])

@app.route('/update_pick', methods=['POST'])
@exception_handler
@check_if_admin
def update_pick(user):
  post = json.loads(request.data)
  return change_pick(post['team_key'], post['overall_pick'], user['yahoo_league_id'], user['draft_id'])

@app.route('/update_pick_enablement', methods=['POST'])
@exception_handler
@check_if_admin
def toggle_pick(user):
  post = json.loads(request.data)
  return toggle_pick_enabled(post['overall_pick'], user['yahoo_league_id'], user['draft_id'])

@app.route('/insert_player', methods=['POST'])
@exception_handler
@check_if_admin
def insert_player(user):
  post = json.loads(request.data)
  return insert_db_player(post['name'], post['player_id'], post['team'], post['positions'], user['draft_id'])

@app.route('/add_keeper_player', methods=['POST'])
@exception_handler
@check_if_admin
def add_keeper_player(user):
  post = json.loads(request.data)
  return add_keeper(post['team_key'], post['player_id'], user['draft_id'])

@app.route('/add_new_pick', methods=['POST'])
@exception_handler
@check_if_admin
def add_new_pick(user):
  post = json.loads(request.data)
  return add_pick_to_draft(user['draft_id'], user['yahoo_league_id'], post['team_key'])

# -------------------------- these routes hit the yahoo api -------------------------- 

# @app.route('/get_teams_in_league')
# def get_teams_in_league():
#   return jsonify({'league': get_team_league_data()})

# @app.route('/get_league')
# def league():
#   return jsonify({'league': get_league()})

# @app.route('/get_yahoo_team_players')
# def get_team_players():
#   return jsonify({'players': get_yahoo_team_players(session['team_id'])})
# @app.route('/test')

# def test():
#   return get_yteam(11)
#   download_players.get_players_from_nhl_draft(2021, 1)
#   return jsonify({"players": download_players.get_players_from_nhl_draft(2021, 2)})
#   # download_players.scrapePlayersFromYahoo()
#   # email_test = emails.next_pick_email('')
  # session['draft_id'] = config.draft_id
#   # return jsonify({"success": email_test})
  # set_draft_picks(14, False)
#   # teams = get_teams_from_db(214)

if __name__== '__main__':
  import credentials
  app.secret_key = credentials.SECRET_KEY

  # get Yahoo Oauth credentials
  config.client_id = credentials.consumer_key
  config.client_secret = credentials.consumer_secret
  config.redirect_uri = "oob"

  # get Yahoo league credentials
  config.league_key = credentials.game_key + ".l." + credentials.yahoo_league_id
  config.yahoo_league_id = credentials.yahoo_league_id
  config.league_id = credentials.league_id
  config.draft_id = credentials.draft_id

  # get Pubnub credentials (for chat)
  config.pubnub_publish_key = credentials.pubnub_publish_key
  config.pubnub_subscribe_key = credentials.pubnub_subscribe_key

  # get local DB credentials
  config.host, config.user, config.password, config.db = credentials.get_local_DB()
  database = db.DB() 

  config.SENDGRID_KEY = credentials.SENDGRID_KEY
  app.run(use_reloader=True, port=5000, threaded=True, debug=True)
else:
  if 'flask_secret_key' in os.environ:
    app.secret_key = os.environ['flask_secret_key']

  if 'client_id' in os.environ:
    config.client_id = os.environ['client_id']
    config.client_secret = os.environ['client_secret']
    config.redirect_uri = "https://slowdraft.herokuapp.com"

  if 'pubnub_publish_key' in os.environ:
    config.pubnub_publish_key = os.environ['pubnub_publish_key']
    config.pubnub_subscribe_key = os.environ['pubnub_subscribe_key']
  
  if 'SENDGRID_KEY' in os.environ:
    config.SENDGRID_KEY = os.environ['SENDGRID_KEY']

	# get Yahoo league credentials
  if 'game_key' in os.environ and 'yahoo_league_id' in os.environ:
    config.league_key = os.environ['game_key'] + ".l." + os.environ['yahoo_league_id']
    config.draft_id = os.environ['draft_id']

  # get DB config
  if 'MYSQL_HOST' in os.environ:
    config.host = os.environ['MYSQL_HOST']
    config.user = os.environ['MYSQL_USER']
    config.password = os.environ['MYSQL_PASSWORD']
    config.db = os.environ['MYSQL_DB']
    database = db.DB()

  if 'yahoo_league_id' in os.environ:
    config.yahoo_league_id = [os.environ['yahoo_league_id']]
    config.league_id = os.environ['league_id']
    config.draft_id = os.environ['draft_id']

  @app.before_request
  def force_https():
    if request.endpoint in app.view_functions and not request.is_secure:
      return redirect(request.url.replace('http://', 'https://'))
