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
from models.rules import *
from models.emails import *
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
      user_id, logo, team_name, league_id, draft_id, role, color = set_team_sessions()
      print(f"user_id: {user_id}")
      print(f"logo: {logo}")
      print(f"team_name: {team_name}")
      print(f"league_id: {league_id}")
      print(f"role: {role}")
      print(f"color: {color}")
      # user = jsonify(
      #   {
      #       'user_id': user_id, 
      #       'logo': logo,
      #       'team_name': team_name, 
      #       'league_id': team_id, 
      #       'role': role, 
      #       'color': color
      #   }
      # )
      # print(f"user: {user}")
      response = jsonify(
        {
          'success': True,
          'access_token': session['access_token'],
          'refresh_token': session['refresh_token'],
          'guid': session['guid'],
          'pub': config.pubnub_publish_key, 
          'sub': config.pubnub_subscribe_key,
          'user': {
            'user_id': user_id, 
            'logo': logo,
            'team_name': team_name, 
            'league_id': league_id, 
            'draft_id': draft_id,
            'role': role, 
            'color': color
          }
        }
      )
      print(f"response: {response}")
          # 'user_id': session['user_id'], 
          # 'logo': str(session['logo']), 
          # 'team_name': session['team_name'], 
          # 'league_id': session['league_id'], 
          # 'role': session['role'], 
          # 'color': session['color']
      return response
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
    print("Access token not in session.")
    return jsonify({'error': 'Not logged in'})
  print("Getting team sessions")
  set_team_sessions()
  return jsonify({'user_id': session['user_id'], 'logo': str(session['logo']), 'team_name': session['team_name'], \
    'league_id': config.league_id, 'role': session['role'], 'color': session['color']})

@app.route('/check_for_updates/<int:user_id>/<int:league_id>')
def check_for_updates_with_user_and_league(user_id, league_id): 
  updates, drafting_now = get_updates_with_league(user_id, league_id)
  return jsonify({'updates': updates, 'drafting_now': drafting_now})

# @app.route('/check_for_updates/<int:user_id>')
# def check_for_updates_with_user(user_id): 
#   updates, drafting_now = get_updates(user_id)
#   return jsonify({'updates': updates, 'drafting_now': drafting_now})

# @app.route('/check_for_updates')
# def check_for_updates(user_id): 
#   print(f"updating for session['user_id']: {session['user_id']}")
#   updates, drafting_now = get_updates(session['user_id'])
#   return jsonify({'updates': updates, 'drafting_now': drafting_now})

# @app.route('/get_teams_in_league')
# def get_teams_in_league():
#   return jsonify({'league': get_team_league_data()})

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

@app.route('/get_db_players/<int:draft_id>')
def get_players_from_db(draft_id):
  position = request.args.get('position', default='skaters')
  exclude_taken_players = request.args.get('exclude_taken', default=True)
  return jsonify({'players': get_db_players(draft_id, position, exclude_taken_players)})

@app.route('/get_forum_posts/<int:league_id>')
def forum(league_id):
  return jsonify({"posts": get_forum_posts(league_id)})

@app.route('/get_all_rules/<int:league_id>')
def get_all_rules(league_id):
  return jsonify({"rules": get_rules(league_id)})

@app.route('/create_rule', methods=['POST'])
def create_rule():
  post = json.loads(request.data)
  new_rule(post)
  return jsonify({"success": True})

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
#   # email_test = emails.next_pick_email('')
#   session['draft_id'] = config.draft_id
#   # return jsonify({"success": email_test})
#   set_draft_picks(14, False)
#   # teams = get_teams_from_db(214)

#   # response = {'test': teams}
#   # return jsonify(response)
#   return jsonify({"success": True})

# Legacy endpoint to avoid interrupting draft for users who don't refresh
@app.route('/get_draft/<int:draft_id>')
def get_draft_picks(draft_id):
  # session['league_id'] = config.league_id
  draft, draft_start_time, draft_picks, current_pick = get_dp(draft_id)
  return jsonify({'draft': draft, 'picks': draft_picks, 'current_pick': current_pick})

@app.route('/get_draft/<int:draft_id>/<int:user_id>')
def get_dps(draft_id, user_id):
  # session['league_id'] = config.league_id
  draft, drafting_now, draft_start_time, draft_picks, current_pick = get_draft(draft_id, user_id)
  if drafting_now == 1:
    drafting_now = True
  else:
    drafting_now = False
  return jsonify({'draft': draft, 'drafting_now': drafting_now, 'picks': draft_picks, 'current_pick': current_pick})

@app.route('/draft/<int:draft_id>/<int:user_id>/<int:player_id>')
def draft_player(draft_id, user_id, player_id):
  player, nextPick, drafting_again = make_pick(draft_id, player_id, user_id)
  drafting_again_text = ''
  if drafting_again == 1:
    drafting_again_text = "You're up again!"

  return jsonify({'player': player, 'next_pick': nextPick, 'drafting_again': drafting_again_text})

@app.route('/update_pick', methods=['POST'])
def update_pick():
  post = json.loads(request.data)
  print(f"post: {post}")
  attempt = False
  try:
    change_pick(post['user_id'], post['overall_pick'], post['league_id'], post['draft_id'])
    return jsonify({'success': True})
  except Exception:
    return jsonify({'success': False})

@app.route('/update_pick_enablement', methods=['POST'])
def disable_pick():
  post = json.loads(request.data)
  print(f"post: {post}")
  attempt = False
  try:
    new_status = toggle_pick_enabled(post['overall_pick'], post['league_id'], post['draft_id'])
    return jsonify({'success': True, 'status': new_status})
  except Exception:
    return jsonify({'success': False})

@app.route('/insert_player', methods=['POST'])
def insert_player():
  post = json.loads(request.data)
  try:
    insert_db_player(post['name'], post['player_id'], post['team'], post['positions'])
    return jsonify({'success': True})
  except Exception as e:
    print("Insert player failed. Error: " + str(e))
    return jsonify({'success': False})

@app.route('/get_teams/<int:draft_id>')
def get_teams(draft_id):
  return jsonify({'teams': get_teams_from_db(draft_id)})

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
