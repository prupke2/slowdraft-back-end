from app import *
# from models.team import *
# from oauth import *
import config
from yahoo_oauth import *
import requests
# import oauth
# oauth.yahoo_oauth import get_access_token, refresh_access_token, test

def yahoo_request(url):
	# pass in a Yahoo fantasy sports URL here
	# this function should only be called after the access and refresh tokens are stored as session variables
	header = "Bearer " + session['access_token']
	print("Attempting to reach URL: %s" % url)
	response = requests.get(url, headers={'Authorization' : header})
	
	if response.status_code == 200:
		payload = xmltodict.parse(response.content)
		print("Success! \n")
		# print(payload)
		return payload
	# a 401 response is expected if the access token has expired.
	# if this happens, use the refresh token to get a new one	
	elif response.status_code == 401 and b"token_expired" in response.content:
		print("Token Expired. Attempting to renew using refresh token.")
		refresh_attempts = 0
		# attempt to get a new token 3 times
		while refresh_attempts < 3:
			refresh_attempts += 1
			print("Attempt # " + str(refresh_attempts))
			refresh = refresh_access_token(config.client_id, config.client_secret, config.redirect_uri)
			if refresh == True:
				break;
		# give up after 3 tries
		if refresh == False:
			session['yahoo'] = False
			return ""
		# if refresh token is obtained, call the function again as it should work now	
		print("Success!")	
		return yahoo_request(url)
	else:
		print("HTTP Code: %s" % response.status_code)
		print("HTTP Response: \n%s" % response.content)
		return ""	

def organize_player_info(player_keys):	
	LEAGUE_URL = YAHOO_BASE_URL + "league/" + config.league_key + "/players;player_keys=" + player_keys
	players = []
	player_query = yahoo_request(LEAGUE_URL)
	try:
		for player in player_query['fantasy_content']['league']['players']['player']:
			player_data = {}
			player_data['player_id'] = player['player_id']
			player_data['player_key'] = str(player['player_key'])
			player_data['name'] = player['name']['full']
			player_data['team'] = player['editorial_team_abbr']
			player_data['position'] = player['eligible_positions']
			players.append(player_data)
	except:
		player_data = {}
		try:
			player_data['player_id'] = player_query['fantasy_content']['league']['players']['player']['player_id']
			player_data['player_key'] = str(player_query['fantasy_content']['league']['players']['player']['player_key'])
			player_data['name'] = player_query['fantasy_content']['league']['players']['player']['name']['full']
			player_data['team'] = player_query['fantasy_content']['league']['players']['player']['editorial_team_abbr']	
			player_data['position'] = player_query['fantasy_content']['league']['players']['player']['eligible_positions']['position']
			players.append(player_data)
		except:
			flash("No players found." , "danger")	
	return players	

def organize_stat_data(stats):	
	# creates new arrays to hold all player stats
	players = []
	player_stats = []	
	# print("\n\nSTATS RECEIVED: " + str(stats))

	try: 
		for stat_set in stats['fantasy_content']['players']['player']:
			# print("\n\nSTAT SET: " + str(stat_set))
			stat_list = stat_set['player_stats']['stats']['stat']

			for stat in stat_list:

				# creates a temporary dictionary for each player's stats which is appended to player_stats[] after each loop
				stat_data = {}
				stat_data['stat_id'] = stat['stat_id']
				stat_data['value'] = stat['value']
				stat_data['player_id'] = stat_set['player_id']

				if stat_set['position_type'] == 'G':
					stat_index = config.GOALIE_STAT_INDEX
				else:
					stat_index = config.SKATER_STAT_INDEX	
					# stat_data['stat'] = 'GOALIE'
				for key in stat_index:
					if key == str(stat_data['stat_id']):
						stat_data['stat'] = stat_index[key]
						player_stats.append(stat_data)				
	except: # this is performed if there is only one result.
		for stat in stats['fantasy_content']['players']['player']['player_stats']['stats']['stat']:
			# creates a temporary dictionary for each player's stats which is appended to player_stats[] after each loop
			stat_data = {}
			stat_data['stat_id'] = stat['stat_id']
			stat_data['value'] = stat['value']
			stat_data['player_id'] = stats['fantasy_content']['players']['player']['player_id']	
			if stats['fantasy_content']['players']['player']['position_type'] == 'G':
				stat_index = GOALIE_STAT_INDEX
			else:
				stat_index = SKATER_STAT_INDEX	
			for key in stat_index:
				if key == str(stat_data['stat_id']):
					stat_data['stat'] = stat_index[key]
					player_stats.append(stat_data)						

	return player_stats				

def organize_player_keys(players):
	keys = ""
	# loops through each player key, separates them with commas, and concatenates them into a string
	# this is the required format to query multiple players in yahoo's API
	for key in players:
		keys+=str(key['player_key'])
		keys+=","
	keys = keys[:-1] # removes the last comma from the end
	return keys

def check_if_prospect(id):
	print("ID: " + str(id))
	database = db.DB()
	sql = "SELECT prospect, careerGP, NHLid FROM yahoo_db_20 WHERE player_id = %s"
	database.cur.execute(sql, [str(id)])
	player = database.cur.fetchone()
	# print(str(result))
	# print("prospect: " + str(prospect) + "\ncareerGP: " + str(careerGP))
	return player['prospect'], player['careerGP'], player['NHLid']	
