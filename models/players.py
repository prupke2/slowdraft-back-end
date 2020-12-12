from app import *
from config import *
import yahoo_api
# from db import *

# Form for searching players
# class PlayerSearchForm(Form):
# 	player_search = StringField('Player', [validators.Length(min=1, max=50)])
# 	# position = SelectField('Position')
# 	showdrafted = BooleanField('showdrafted')

# def getDBPlayers(sortby, sortdir, position, player_search, offset):
# 	database = db.DB()
# 	sql_base = "SELECT * FROM yahoo_db_19 y "
# 	exclude_taken_players = "WHERE NOT EXISTS (SELECT player_id FROM user_team ut WHERE ut.player_id = y.player_id) "
# 	include_taken_players = "LEFT JOIN user_team ut ON ut.player_id = y.player_id LEFT JOIN users u ON u.user_id = ut.user_id"
# 	# if (position == 'G' or position == 'goalie_prospects') and sortby not in GOALIE_STAT_INDEX:
# 	# 	sortby = 19 
# 	# if (position != 'G' and position != 'goalie_prospects') and sortby not in SKATER_STAT_INDEX:
# 	# 	sortby = 3 	
# 	if position != None or player_search != '':
# 		if player_search != '':
# 			where = " WHERE y.name LIKE '%" + str(player_search) + "%'"
# 		else:
# 			if position == 'LW,RW,C':
# 				where = "AND ((position LIKE '%LW%') OR (position LIKE '%RW%') OR (position LIKE '%C%')) "
# 			elif position == "LW,RW":
# 				where = "AND ((position LIKE '%LW%') OR (position LIKE '%RW%')) "	
# 			elif position == "prospects":
# 				where = "AND position != 'G' AND prospect = 1"
# 			elif position == "goalie_prospects":	
# 				where = "AND position = 'G' AND prospect = 1"
# 			elif position == "multi":
# 				where = "AND (LENGTH(position) > 2)"	
# 			else:
# 				where = "AND position LIKE '%" + str(position) + "%' "

# 	else:
# 		where = ""		
# 	if sortby:
# 		if sortdir:
# 			if sortdir == '1':
# 				sortdir = 'ASC'
# 				if sortby == '23':
# 					where += " AND `18` >= 10" # requires 10 games started when sorting goalies by GAA
# 			else:
# 				sortdir = 'DESC'	
# 		else:
# 			sortdir = 'DESC'	

# 		order = " ORDER BY `" + str(sortby) + "` " + sortdir
# 	else:
# 		order = ""	
# 	if player_search:
# 		sql = sql_base + include_taken_players + where + order + " LIMIT 100"
# 	else:
# 		sql = sql_base + exclude_taken_players + where + order + " LIMIT 25 OFFSET " + str(offset)
# 	print(str(sql))
# 	result = database.cur.execute(sql)	
# 	players = database.cur.fetchall()
# 	# print(str(players))
# 	skaters = []
# 	goalies = []
# 	for player in players:
# 		if player['position'] == 'G':
# 			goalies.append(player)
# 		else:
# 			skaters.append(player)	
# 	return skaters, goalies

def get_players(sortby, sortdir, position, player_search, offset):
	LEAGUE_URL = YAHOO_BASE_URL + "league/" + config.league_key
	# all_free_agents = yahoo_request(YAHOO_BASE_URL + "league/" + config.league_key + "/players;status=FA;count=22")
	if player_search != '':
		player_query = yahoo_api.yahoo_request(LEAGUE_URL + '/players;search=' + str(player_search))
	else:
		player_query = yahoo_api.yahoo_request(LEAGUE_URL + "/players?status=A&position=" + position + "&sort=" + str(sortby) \
		+ "&sdir=" + str(sortdir) + "&start=" + str(offset) + "&count=25;sorttype=season")

	# print("\n\nQUERY: " + str(player_query))

	skaters = []
	goalies = []
	# loops through the players and stores player info in new arrays
	try:
		for player in player_query['fantasy_content']['league']['players']['player']:
			player_data = {}
			player_data['player_id'] = player['player_id']
			player_data['player_key'] = str(player['player_key'])
			player_data['name'] = player['name']['full']
			player_data['team'] = player['editorial_team_abbr']
			player_data['position'] = player['eligible_positions']

			if player['display_position'] == 'G':
				goalies.append(player_data)
			else:
				skaters.append(player_data)
	except:
		player_data = {}
		try:
			player_data['player_id'] = player_query['fantasy_content']['league']['players']['player']['player_id']
			player_data['player_key'] = str(player_query['fantasy_content']['league']['players']['player']['player_key'])
			player_data['name'] = player_query['fantasy_content']['league']['players']['player']['name']['full']
			player_data['team'] = player_query['fantasy_content']['league']['players']['player']['editorial_team_abbr']	
			player_data['position'] = player_query['fantasy_content']['league']['players']['player']['eligible_positions']['position']

			if player['display_position'] == 'G':
				goalies.append(player_data)
			else:
				skaters.append(player_data)
		except:
			flash("No players found." , "danger")		
			
	if skaters == []:	
		skater_stats=''
	else:	
		skater_keys = yahoo_api.organize_player_keys(skaters)
		MY_PLAYERS_URL = YAHOO_BASE_URL + "players;player_keys=" + skater_keys + "/stats;date=2018"
		my_skater_stats = yahoo_api.yahoo_request(MY_PLAYERS_URL)
		# print("\n\nPlayers: " + str(skaters))
		# print("\n\nPlayer stats: " + str(my_skater_stats))
		skater_stats = yahoo_api.organize_stat_data(my_skater_stats)

	if goalies == []:
		goalie_stats = ''
	else:			
		goalie_keys = yahoo_api.organize_player_keys(goalies)
		MY_GOALIES_URL = YAHOO_BASE_URL + "players;player_keys=" + goalie_keys + "/stats;date=2018"
		my_goalie_stats = yahoo_api.yahoo_request(MY_GOALIES_URL)
		# print("\n\nGoalies: " + str(goalies))
		# print("\n\nGoalie URL: " + str(MY_GOALIES_URL))
		# print("\n\nGoalie stats: " + str(my_goalie_stats))
		# goalie_stats = my_goalie_stats
		goalie_stats = yahoo_api.organize_stat_data(my_goalie_stats)
	# except:
	# 	flash('No players found.', 'danger')
	# 	return '', '', '', ''

	return skaters, skater_stats, goalies, goalie_stats

def getPlayersFromDBAndYahoo(sortby, sortdir, position, player_search, offset):
	skaters, goalies = getDBPlayers(sortby, sortdir, position, player_search, offset)

	if skaters == []:	
		skater_stats = ''
		skater_info = ''
	else:	
		skater_keys = yahoo_api.organize_player_keys(skaters)
		skater_info = organizePlayerInfo(skater_keys)
		print("INFO: " + str(skater_info))

		MY_PLAYERS_URL = YAHOO_BASE_URL + "players;player_keys=" + skater_keys + "/stats;date=2018"
		my_skater_stats = yahoo_api.yahoo_request(MY_PLAYERS_URL)
		# print("\n\nPlayers: " + str(skaters))
		# print("\n\nPlayer stats: " + str(my_skater_stats))
		skater_stats = yahoo_api.organize_stat_data(my_skater_stats)
		# for skater in skater_info:
		# 	for skater_stat in skater_stats:
		# 		if skater_stat['player_id'] == skater['player_id']:
		# 			skater_stats.append(skater['position'])

	if goalies == []:
		goalie_stats = ''
		goalie_info = ''
	else:			
		goalie_info = organizePlayerInfo(goalies)
		goalie_keys = yahoo_api.organize_player_keys(goalies)
		MY_GOALIES_URL = YAHOO_BASE_URL + "players;player_keys=" + goalie_keys + "/stats;date=2018"
		my_goalie_stats = yahoo_api.yahoo_request(MY_GOALIES_URL)
		# print("\n\nGoalies: " + str(goalies))
		# print("\n\nGoalie URL: " + str(MY_GOALIES_URL))
		# print("\n\nGoalie stats: " + str(my_goalie_stats))
		# goalie_stats = my_goalie_stats
		goalie_stats = yahoo_api.organize_stat_data(my_goalie_stats)
	return skaters, skater_info, skater_stats, goalies, goalie_info, goalie_stats

		