import config
import base64
import requests
from app import *

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
	# this function will only run if your team_id isn't already set 
	if team_id is not None:	
		TEAM_URL = config.YAHOO_BASE_URL + "league/" + config.league_key + "/teams"
		team_query = yahoo_api.yahoo_request(TEAM_URL)
		session['yahoo_league_id'] = team_query['fantasy_content']['league']['league_id']
		teams = []
		for team in team_query['fantasy_content']['league']['teams']['team']:
			team_data = {}
			# # print("TEAM: " + str(team))
			# team_data['team_id'] = team['team_id']
			# team_data['user'] = team['managers']['manager']['nickname']
			# team_data['user_logo'] = team['managers']['manager']['image_url']
			# team_data['team_name'] = team['name']
			# team_data['team_logo'] = team['team_logos']['team_logo']['url']
			# team_data['waiver_priority'] = team['waiver_priority']

			# # some managers choose not to share their email, so this sets it to empty if that is the case
			# try:
			# 	team_data['email'] = team['managers']['manager']['email']
			# except:
			# 	team_data['email'] = ""	

			if session['guid'] == team['managers']['manager']['guid']:
				print(f"team: {team}")
				session['team_id'] = team['team_id']
				session['logo'] = team['team_logos']['team_logo']['url']
				session['team_name'] = team['name']
				# if ('user_id' not in session) or ('role' not in session):
				database = db.DB()
				sql = "SELECT * FROM users WHERE yahoo_league_id = %s AND yahoo_team_id = %s"
				database.cur.execute(sql, (session['yahoo_league_id'], session['team_id']))
				user = database.cur.fetchone()
				session['user_id'] = user['user_id']
				session['role'] = user['role']
				session['league_id'] = user['league_id']
				session['color'] = user['color']
				# config.team_id = team['team_id']

			# teams.append(team_data)

	return

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
