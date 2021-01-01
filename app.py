from flask import Flask, request, send_from_directory, session, request, url_for, redirect, render_template, jsonify, flash, send_from_directory
from oauth import *
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
from yahoo_api import *
import db
import datetime
import pymysql
# import download_players

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
  if code != '':
    response = get_access_token(config.client_id, config.client_secret, config.redirect_uri, code)
    if response == True:
      return jsonify(
        {
          'success': True,
          'access_token': session['access_token'],
          'refresh_token': session['refresh_token'],
          'guid': session['guid'],
          'pub': config.pubnub_publish_key, 
          'sub': config.pubnub_subscribe_key
        }
      ) 
    else:
      return jsonify(
        {
          'success': False,
          'error': response
        }
      ) 
  else:
    print('Warning: No code provided.')
    return jsonify({'response': 'No code provided'}) 

@app.route('/check_login')
def check_login():
  if 'access_token' in session and 'refresh_token' in session:
    # On successful login, return Pubnub keys for chat backend
    return jsonify(
      {
        'success': True, 
        'pub': config.pubnub_publish_key, 
        'sub': config.pubnub_subscribe_key
      }
    )
  return jsonify(
    {
      'success': False, 
      'error': 'Unable to get access token'
    }
  )

@app.route('/get_team_session')
def get_team_session():
  if 'access_token' not in session:
    return jsonify({'error': 'Not logged in'})
  print("Getting team sessions")
  set_team_sessions()
  return jsonify({'user_id': session['user_id'], 'logo': session['logo'], 'team_name': session['team_name']})

# @app.route('/get_teams_in_league')
# def get_teams():
#   return jsonify({'league': get_teams_in_league()})

@app.route('/get_league')
def league():
  return jsonify({'league': get_league()})

# @app.route('/get_players')
# def players():
#   sortby = request.args.get('sortby', default=3)
#   sortdir = request.args.get('sortdir', default=0)
#   position = request.args.get('position', default='LW,RW,C')
#   player_search = request.args.get('player_search', default='')
#   showdrafted = request.args.get('showdrafted', default='False')
#   offset = request.args.get('offset', default='0')
#   skaters, skater_stats, goalies, goalie_stats = get_players(sortby, sortdir, position, player_search, offset)
#   return jsonify({'players': skaters})

# @app.route('/get_yahoo_team_players')
# def get_team_players():
#   return jsonify({'players': get_yahoo_team_players(session['team_id'])})

@app.route('/get_db_players')
def get_players_from_db():
  if 'draft_id' not in session:
    session['draft_id'] = config.draft_id
  position = request.args.get('position', default='skaters')
  exclude_taken_players = request.args.get('exclude_taken', default=True)
  return jsonify({'players': get_db_players(position, exclude_taken_players)})

@app.route('/get_forum_posts')
def forum():
  return jsonify({"posts": get_forum_posts()})

@app.route('/view_post_replies/<int:post_id>')
def view_forum_post(post_id):
  return jsonify({"replies": view_post_replies(post_id)})

@app.route('/new_forum_post', methods=['POST'])
def post_to_forum():
  print("new_forum_post hit")
  post = json.loads(request.data)
  print(f"post: {post}")
  print(f"post title: {post['title']}")
  new_forum_post(post)
  return jsonify({"success": True})

# @app.route('/test')
# def test():
#   # download_players.scrapePlayersFromYahoo()
#   session['draft_id'] = config.draft_id
#   # set_draft_picks(14, False)
#   teams = get_teams_from_db()

#   response = {'test': teams}
#   return jsonify(response)

@app.route('/get_draft')
def get_draft_picks():
  if 'role' not in session:
    session['role'] = 'admin'
  session['league_id'] = config.league_id
  draft, draft_start_time, draft_picks, current_pick = get_draft()
  return jsonify({'draft': draft, 'picks': draft_picks, 'current_pick': current_pick, 'role': session['role']})

@app.route('/draft/<int:player_id>')
def draft_player(player_id):
  player, nextPick, draftingAgain = make_pick(player_id, session['user_id'])
  return jsonify({'player': player, 'next_pick': nextPick, 'drafting_again': draftingAgain})

@app.route('/update_pick', methods=['POST'])
def update_pick():
  post = json.loads(request.data)
  print(f"post: {post}")
  change_pick(post['user_id'], post['overall_pick'])
  return jsonify({'success': True})

@app.route('/get_teams')
def get_teams():
  if 'draft_id' not in session:
    session['draft_id'] = config.draft_id
  return jsonify({'teams': get_teams_from_db()})

if __name__== '__main__':
  import credentials
  app.secret_key = credentials.SECRET_KEY

  # get Yahoo Oauth credentials
  config.client_id = credentials.consumer_key
  config.client_secret = credentials.consumer_secret
  config.redirect_uri = "oob"

  # get Yahoo league credentials
  config.league_key = credentials.game_key + ".l." + credentials.yahoo_league_id

  # get Pubnub credentials (for chat)
  config.pubnub_publish_key = credentials.pubnub_publish_key
  config.pubnub_subscribe_key = credentials.pubnub_subscribe_key

  # get local DB credentials
  config.host, config.user, config.password, config.db = credentials.get_local_DB()
  database = db.DB() 

  config.yahoo_league_id = credentials.yahoo_league_id
  config.league_id = credentials.league_id
  config.draft_id = credentials.draft_id

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
  @app.before_request
  def force_https():
    if request.endpoint in app.view_functions and not request.is_secure:
      return redirect(request.url.replace('http://', 'https://'))
