from app import *
from config import *
import yahoo_api
import db
# import oauth
import config
# from wtforms import Form, HiddenField
# from nhl_api import checkIfProspect

# class save_keepersForm(Form):
# 	keys_input = HiddenField('keys_input')

def get_teams_from_db(draft_id):
	database = db.DB()
	sql = "SELECT u.yahoo_team_id, u.username, ut.is_keeper, y.name, y.team, y.position, y.prospect, y.player_id, y.headshot \
			FROM user_team ut \
			JOIN yahoo_db_21 y ON y.player_id = ut.player_id \
			JOIN users u ON ut.team_key = u.team_key \
			WHERE draft_id = %s \
			ORDER BY u.yahoo_team_id, FIELD(y.position, 'LW', 'C', 'RW', 'RW/C', 'RW/LW', \
				 'C/LW/RW', 'C/LW', 'C/RW', 'LW/RW', 'LW/C', 'LW/D', 'D/LW', 'RW/D', 'D/RW', 'D')"
	database.cur.execute(sql, (draft_id))
	players = database.cur.fetchall()	
	return players

def get_yahoo_team(team_id):
	ROSTER_URL = YAHOO_BASE_URL + "team/" + config.league_key + ".t." + team_id + "/roster"
	roster = yahoo_api.yahoo_request(ROSTER_URL)
	if roster == '':
		return '','','','';	

	my_skaters = []
	my_goalies = []
	return roster['fantasy_content']['team']['name']		

def get_yahoo_team_players(team_id):
 
	ROSTER_URL = f"{YAHOO_BASE_URL}/team/{config.league_key}.t.{str(team_id)}/roster"
	roster = yahoo_api.yahoo_request(ROSTER_URL)
	if roster == '':
		return '','','','';	

	my_skaters = []
	my_goalies = []
	team = roster['fantasy_content']['team']['name']
	for player in roster['fantasy_content']['team']['roster']['players']['player']:
		player_data = {}
		player_data['player_id'] = str(player['player_id'])
		prospect, careerGP, NHLid = yahoo_api.checkIfProspect(player_data['player_id'])
		player_data['prospect'] = prospect
		player_data['careerGP'] = careerGP
		player_data['NHLid'] = NHLid
		player_data['player_key'] = player['player_key']
		player_data['name'] = player['name']['full']
		player_data['team'] = player['editorial_team_abbr']
		player_data['position'] = player['eligible_positions']
		if player['position_type'] == 'G':
			my_goalies.append(player_data)
		else:
			my_skaters.append(player_data)

	skater_keys = yahoo_api.organize_player_keys(my_skaters)	
	goalie_keys = yahoo_api.organize_player_keys(my_goalies)	

	# print("\n\nGOALIE KEYS: " + goalie_keys)

	MY_SKATERS_URL = YAHOO_BASE_URL + "players;player_keys=" + skater_keys + "/stats;date=2018"
	my_skater_stats = yahoo_api.yahoo_request(MY_SKATERS_URL)

	MY_GOALIES_URL = YAHOO_BASE_URL + "players;player_keys=" + goalie_keys + "/stats;date=2018"
	my_goalie_stats = yahoo_api.yahoo_request(MY_GOALIES_URL)

	skater_stats = yahoo_api.organizeStatData(my_skater_stats)
	goalie_stats = yahoo_api.organizeStatData(my_goalie_stats)

	return team, my_skaters, skater_stats, my_goalies, goalie_stats

def get_user_id():
	database = db.DB()
	sql = "SELECT user_id, time_zone_offset FROM users WHERE yahoo_league_id = %s AND yahoo_team_id = %s"
	database.cur.execute(sql, (session['yahoo_league_id'], session['team_id']))
	result = database.cur.fetchone()
	session['user_id'] = result['user_id']
	session['time_zone_offset'] = result['time_zone_offset']

def set_new_user_id(team_id):
	database = db.DB()
	sql = "SELECT user_id, username FROM users WHERE yahoo_league_id = %s AND yahoo_team_id = %s"
	query = database.cur.execute(sql, (session['yahoo_league_id'], team_id))
	result = database.cur.fetchone()	
	if result is not None:
		session['user_id'] = result['user_id']
		session['team_id'] = team_id
		return str(session['user_id']), str(result['username'])
	else:
		return False, False

def check_if_keepers(team_id):
	database = db.DB()
	sql = "SELECT player_id FROM user_team WHERE user_id = %s AND draft_id = %s"
	sql = "SELECT player_id FROM user_team ut INNER JOIN users u ON u.user_id = ut.user_id WHERE u.yahoo_team_id = %s AND ut.draft_id = %s"
	database.cur.execute(sql, (team_id, session['draft_id']))
	return database.cur.fetchall()	

def check_validity_of_keepers(keys):
	database = db.DB()
	sql = "SELECT * FROM yahoo_db_21 WHERE player_id IN (" + keys + ")"
	result = database.cur.execute(sql)
	keepers = database.cur.fetchall()
	goalies = 0
	nonProspects = 0
	total = 0
	errors = ""
	for player in keepers:
		total += 1
		if player['prospect'] == '0':
			nonProspects += 1
		if player['position'] == 'G':
			goalies += 1
	if total >=11 or nonProspects >= 8 or goalies >= 3:
		errors = "Unable to save keepers:"		
		if total >= 11:
			errors += " Too many keepers saved (maximum 10)."	
		if nonProspects >= 8:
			errors += " Too many non-prospect keepers selected: you must keep at least 3 prospects."	
		if goalies >= 3:
			errors += " Too many goalie keepers selected: you may only keep two goalies."
		print
		return errors, False
	else:
		return keepers, True		
			
def delete_keepers():
	database = db.DB()
	sql = "DELETE FROM user_team WHERE user_id = %s AND draft_id = %s"		
	database.cur.execute(sql, (session['user_id'], session['draft_id']))
	database.connection.commit()


def save_keepers(keepers):
	database = db.DB()
	for keeper in keepers:
		sql = "INSERT INTO user_team(user_id, draft_id, player_id, is_keeper, NHLid) VALUES(%s, %s, %s, %s, %s)"
		print("\n\n Query: " + str(sql))
		database.cur.execute(sql, (session['user_id'], session['draft_id'], keeper['player_id'], 1, keeper['NHLid']))
		database.connection.commit()

def add_keeper(team_key, player_id, draft_id):
	# print(f"user_id: {user_id}, player_id: {player_id}, draft_id: {draft_id} ")
	database = db.DB()
	sql = "INSERT INTO user_team(team_key, draft_id, player_id, is_keeper, NHLid) VALUES(%s, %s, %s, %s, %s)"
	database.cur.execute(sql, (team_key, draft_id, player_id, 1, 0))
	database.connection.commit()
