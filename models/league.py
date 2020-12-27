from app import *
from config import *
import yahoo_api
import oauth.yahoo_oauth
import db


def get_teams_in_league():
	# this function will only run if your team_id isn't already set 
	if team_id == '':	
		TEAM_URL = YAHOO_BASE_URL + "league/" + config.league_key + "/teams"
		team_query = yahoo_api.yahoo_request(TEAM_URL)	
		session['yahoo_league_id'] = team_query['fantasy_content']['league']['league_id']
		teams = []
		for team in team_query['fantasy_content']['league']['teams']['team']:
			team_data = {}
			# print("TEAM: " + str(team))
			team_data['team_id'] = team['team_id']
			team_data['user'] = team['managers']['manager']['nickname']
			team_data['user_logo'] = team['managers']['manager']['image_url']
			team_data['team_name'] = team['name']
			team_data['team_logo'] = team['team_logos']['team_logo']['url']
			team_data['waiver_priority'] = team['waiver_priority']

			# some managers choose not to share their email, so this sets it to empty if that is the case
			try:
				team_data['email'] = team['managers']['manager']['email']
			except:
				team_data['email'] = ""	

			if session['guid'] == team['managers']['manager']['guid']:
				session['team_id'] = team['team_id']
				print(f"team['team_id']: {team['team_id']}")
				session['logo'] = team_data['team_logo']
				session['team_name'] = team_data['team_name']
				# if ('user_id' not in session) or ('role' not in session):
				database = db.DB()
				sql = "SELECT * FROM users WHERE yahoo_league_id = %s AND yahoo_team_id = %s"
				print(f"session['yahoo_league_id']: {session['yahoo_league_id']}")
				database.cur.execute(sql, (session['yahoo_league_id'], session['team_id']))
				user = database.cur.fetchone()
				if user is None:
					print(f"No user found with yahoo_league_id #{session['yahoo_league_id']}")
				else:
					session['user_id'] = user['user_id']
					session['role'] = user['role']
					session['league_id'] = user['league_id']
					session['color'] = user['color']
					# config.team_id = team['team_id']

			teams.append(team_data)

	return teams

	# https://fantasysports.yahooapis.com/fantasy/v2/league/386.l.18571/teams

def get_league():
	LEAGUE_URL = YAHOO_BASE_URL + 'league/' + config.league_key + '/settings'
	league_query = yahoo_api.yahoo_request(LEAGUE_URL)
	# print(league_query)
	if league_query == '':
		error = 'Unable to access Yahoo.'
		return jsonify({'success': False, 'error': error})
	league_data = league_query['fantasy_content']['league']
	league = {}
	league['logo'] = league_data['logo_url']
	league['league_id'] = league_data['league_id']
	league['league_name'] = league_data['name']
	league['positions'] = league_data['settings']['roster_positions']['roster_position']	
	config.league_data = league_data
	return league	
