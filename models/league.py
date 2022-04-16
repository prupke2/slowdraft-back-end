from app import *
from config import *
import yahoo_api
import oauth.yahoo_oauth
import db
import util


def get_leagues(access_token, refresh_token):
		GET_LEAGUES_URL = YAHOO_BASE_URL + 'users;use_login=1/games;game_keys=411/leagues'
		print(f"GET_LEAGUES_URL: {GET_LEAGUES_URL}")
		try:
				leagues_query = yahoo_api.yahoo_request(GET_LEAGUES_URL, access_token, refresh_token, True)
				# print(f"leagues_query: {leagues_query}")
				user = leagues_query['fantasy_content']['users']['0']['user']
				# print(f"user: {user}")
				leagues = user[1]['games']['0']['game'][1]['leagues']
				# print(f"leagues: {leagues}")
				league_count = leagues['count']
				if league_count == 0:
						return []
				league_list = []
				for i in range(league_count):
						league_list.append(leagues[str(i)]['league'][0])
				return league_list
		except Exception as e:
				print(f"Error in get_leagues function: {e}")
				return []


def register_leagues(access_token, refresh_token):
    leagues = get_leagues(access_token, refresh_token)
    league_list, registered_count = check_league_registrations(leagues)
    if registered_count == 1:
        league_key = get_registered_league(league_list)
        team_query = get_teams_in_league(
            league_key, access_token, refresh_token)
        teams, my_team_data, is_live_draft, registered = models.status.set_team_sessions(
            league_key, team_query)
        web_token = generate_web_token(
            leagues, my_team_data, access_token, refresh_token)
    else:
        my_team_data = None
        teams = None
        is_live_draft = None
        registered = registered_count > 0
        web_token = generate_temp_web_token(
            league_list, access_token, refresh_token)
    print(f"\nNEW LOGIN: {my_team_data}\n")

    return jsonify({
        'success': True,
        'pub': config.pubnub_publish_key,
        'sub': config.pubnub_subscribe_key,
        'league_list': league_list,
        'user': my_team_data,
        'teams': teams,
        'web_token': web_token,
        'is_live_draft': is_live_draft,
        'registered': registered
    })


def get_registered_league(league_list):
    for league in league_list:
        if league['registered'] == True:
            return league['league_key']


def validate_league_key(league_list, league_key):
    for league in league_list:
        if league['league_key'] == league_key:
            return True
    return False


def check_league_registrations(leagues):
    database = db.DB()
    yahoo_league_id_list = []
    for league in leagues:
        yahoo_league_id_list.append(league['league_id'])

    league_list = str(yahoo_league_id_list)[1:-1]
    sql = f"""
			SELECT yahoo_league_id
			FROM yahoo_league
			WHERE yahoo_league_id IN ({league_list})
		"""
    database.cur.execute(sql)
    leagues_query = database.cur.fetchall()
    registered_leagues = []
    for i, league in enumerate(leagues_query):
        registered_leagues.append(leagues_query[i]['yahoo_league_id'])
    for league in leagues:
        league['registered'] = int(league['league_id']) in registered_leagues
    print(f"\n\nLEAGUES: {leagues}\n\n")
    return leagues, len(registered_leagues)


def select_league(user, league_key):

		league_check = validate_league_key(user['leagues'], league_key)
		if league_check == False:
				util.return_error('invalid_league', 403)

		try:
				team_query = get_teams_in_league(
						league_key, user['access_token'], user['refresh_token'])
				print(f"team_query: {team_query}")
				teams, my_team_data, is_live_draft, registered = models.status.set_team_sessions(
						league_key, team_query)
				print(f"\n\nmy_team_data: {my_team_data}")
				web_token = generate_web_token(
						user['leagues'], my_team_data, user['access_token'], user['refresh_token'])
				return jsonify({
						'success': True,
						'user': my_team_data,
						'teams': teams,
						'web_token': web_token,
						'is_live_draft': is_live_draft,
						'registered': registered
				})
		except Exception as e:
				print(f"Error in select_league: {e}")


def get_teams_in_league(league_key, access_token, refresh_token):
    TEAM_URL = config.YAHOO_BASE_URL + "league/" + league_key + "/teams"
    try:
        team_query = yahoo_api.yahoo_request(
            TEAM_URL, access_token, refresh_token)
        return team_query
    except Exception as e:
        print(f"Error in get_teams_in_league: {e}")


# def get_teams_in_league():
#     # this function will only run if your team_id isn't already set
#     if team_id == '':
#         TEAM_URL = YAHOO_BASE_URL + "league/" + config.league_key + "/teams"
#         team_query = yahoo_api.yahoo_request(TEAM_URL)
#         session['yahoo_league_id'] = team_query['fantasy_content']['league']['league_id']
#         teams = []
#         for team in team_query['fantasy_content']['league']['teams']['team']:
#             team_data = {}
#             # print("TEAM: " + str(team))
#             team_data['team_id'] = team['team_id']
#             team_data['user'] = team['managers']['manager']['nickname']
#             team_data['user_logo'] = team['managers']['manager']['image_url']
#             team_data['team_name'] = team['name']
#             team_data['team_logo'] = team['team_logos']['team_logo']['url']
#             team_data['waiver_priority'] = team['waiver_priority']

#             # some managers choose not to share their email, so this sets it to empty if that is the case
#             try:
#                 team_data['email'] = team['managers']['manager']['email']
#             except:
#                 team_data['email'] = ""

#             if session['guid'] == team['managers']['manager']['guid']:
#                 session['team_id'] = team['team_id']
#                 print(f"team['team_id']: {team['team_id']}")
#                 session['logo'] = team_data['team_logo']
#                 session['team_name'] = team_data['team_name']
#                 # if ('user_id' not in session) or ('role' not in session):
#                 database = db.DB()
#                 sql = "SELECT * FROM users WHERE yahoo_league_id = %s AND yahoo_team_id = %s"
#                 print(
#                     f"session['yahoo_league_id']: {session['yahoo_league_id']}")
#                 database.cur.execute(
#                     sql, (session['yahoo_league_id'], session['team_id']))
#                 user = database.cur.fetchone()
#                 if user is None:
#                     print(
#                         f"No user found with yahoo_league_id #{session['yahoo_league_id']}")
#                 else:
#                     session['user_id'] = user['user_id']
#                     session['role'] = user['role']
#                     session['league_id'] = user['league_id']
#                     session['color'] = user['color']
#                     # config.team_id = team['team_id']

#             teams.append(team_data)

#     return teams

    # https://fantasysports.yahooapis.com/fantasy/v2/league/386.l.18571/teams


# def get_league():
#     LEAGUE_URL = YAHOO_BASE_URL + 'league/' + config.league_key + '/settings'
#     league_query = yahoo_api.yahoo_request(LEAGUE_URL)
#     # print(league_query)
#     if league_query == '':
#         error = 'Unable to access Yahoo.'
#         return jsonify({'success': False, 'error': error})
#     league_data = league_query['fantasy_content']['league']
#     league = {}
#     league['logo'] = league_data['logo_url']
#     league['league_id'] = league_data['league_id']
#     league['league_name'] = league_data['name']
#     league['positions'] = league_data['settings']['roster_positions']['roster_position']
#     config.league_data = league_data
#     return league
