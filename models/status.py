import config
import base64
import requests
from flask import jsonify
from app import *
import yahoo_api
import db

def get_updates_with_league(yahoo_league_id, team_key):
	database = db.DB()
	database.cur.execute("SELECT * FROM updates WHERE yahoo_league_id = %s", yahoo_league_id)
	updates = database.cur.fetchone()
	return jsonify({'updates': updates, 'drafting_now': check_if_drafting(database, team_key)})

def check_if_drafting(database, team_key):
	sql = "SELECT drafting_now FROM users WHERE team_key = %s"
	database.cur.execute(sql, team_key)
	result = database.cur.fetchone()
	if result and result['drafting_now'] == 1:
		return True
	return False
	
# Makes sure the draft session variable is set
def check_league(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'draft_id' not in session:
			database = db.DB()
			sql = "SELECT * FROM league WHERE yahoo_league_id = %s"
			league_id = str(config.league_key[-5:])
			result = database.cur.execute(sql, league_id)
			league = database.cur.fetchone()
			session['draft_id'] = league['most_recent_draft_id']

		return f(*args, **kwargs)
	return wrap		


def set_team_sessions():
	my_team_data = {}
	TEAM_URL = config.YAHOO_BASE_URL + "league/" + config.league_key + "/teams"
	team_query = yahoo_api.yahoo_request(TEAM_URL)
	my_team_data['yahoo_league_id'] = team_query['fantasy_content']['league']['league_id']
	teams = []
	for team in team_query['fantasy_content']['league']['teams']['team']:
		team_data = {}
		# print("TEAM: " + str(team))
		team_data['team_id'] = team['team_id']
		team_data['team_key'] = team['team_key']
		team_data['user'] = team['managers']['manager']['nickname']
		team_data['user_logo'] = team['managers']['manager']['image_url']
		team_data['team_name'] = team['name']
		team_data['team_logo'] = team['team_logos']['team_logo']['url']
		# team_data['waiver_priority'] = team['waiver_priority']

		# # some managers choose not to share their email, so this sets it to empty if that is the case
		# try:
		# 	team_data['email'] = team['managers']['manager']['email']
		# except:
		# 	team_data['email'] = ""	

		if 'is_owned_by_current_login' in team:
		# if session['guid'] == team['managers']['manager']['guid']:
			print(f"team: {team}")
			my_team_data['team_id'] = team['team_id']
			my_team_data['logo'] = team['team_logos']['team_logo']['url']
			my_team_data['team_name'] = team['name']
			my_team_data['team_key'] = team['team_key']
			database = db.DB()
			sql = """
				SELECT u.role, u.color, d.draft_id, d.current_pick
				FROM users u
				INNER JOIN draft d
					ON u.yahoo_league_id = d.yahoo_league_id
				WHERE team_key = %s
			"""
			database.cur.execute(sql, [my_team_data['team_key']])
			user = database.cur.fetchone()
			my_team_data['role'] = user['role']
			my_team_data['color'] = user['color']
			my_team_data['draft_id'] = user['draft_id']
			my_team_data['current_pick'] = user['current_pick']
		teams.append(team_data)
	return teams, my_team_data

def check_draft_status(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		database = db.DB()
		# draft.checkCurrentPickInDraft()
		sql = "SELECT * FROM draft d LEFT JOIN draft_picks dp ON d.draft_id = dp.draft_id WHERE d.draft_id = %s ORDER BY dp.overall_pick"
		database.cur.execute(sql, session['draft_id'])
		print("DRAFT ID: " + str(session['draft_id']))
		draft_info = database.cur.fetchone()
		print("info: \n" + str(draft_info))
		if draft_info['is_live'] == 1:
			session['current_pick'] = draft.getCurrentPickInfo(draft_info['current_pick'])
		else:
			session['current_pick'] = 0	

		draft_start_time = draft_info['draft_start_time_utc']
		if (draft_info['is_live'] == 0) and (draft_start_time < datetime.datetime.utcnow() and draft_info['is_over'] == 0):
			sql = "UPDATE draft SET is_live=1, current_pick = 1 WHERE draft_id = %s"
			database.cur.execute(sql, session['draft_id'])
			database.connection.commit()
			sql = "UPDATE users SET drafting_now = 1 WHERE user_id = %s"
			print("USER ID: " + str(draft_info['user_id']))
			database.cur.execute(sql, draft_info['user_id'])
			database.connection.commit()
		# print("IS OVER? : " + str(draft_info['is_over']))	
		if draft_info['is_over'] == 1:
			session['current_pick'] = None
		return f(*args, **kwargs)
	return wrap		
