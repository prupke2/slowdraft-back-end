import os

site = "https://slowdraft.herokuapp.com"
teams = []
league_data = []

# DB variables
conn = ''

# Twilio settings (for SMSes)
account_sid = ''
auth_token = ''
twilio = ''

# number for sending test SMSes
# if 'test_number' in os.environ:
# 	test_number = os.environ['test_number']
# else:
# 	import credentials
# 	test_number = credentials.test_number	

# Sendgrid settings (for emails)
mail_server = ''
mail_port = 465
mail_username = ''
mail_password = ''
mail_use_tls = False
mail_use_ssl = True

sendgrid_key = ''

# NHL.com API endpoints and team IDs
NEXT_GAME_URL = "https://statsapi.web.nhl.com/api/v1/teams/%s?expand=team.schedule.next"
NHL_TEAM_ID = {
    'New Jersey Devils' : '1',
    'New York Islanders' : '2',
    'New York Rangers' : '3',
    'Philadelphia Flyers' : '4',
    'Pittsburgh Penguins' : '5',
    'Boston Bruins' : '6',
    'Buffalo Sabres' : '7',
    'Montreal Canadiens' : '8',
    'Ottawa Senators' : '9',
    'Toronto Maple Leafs' : '10',
    'Carolina Hurricanes' : '12',
    'Florida Panthers' : '13',
    'Tampa Bay Lightning' : '14',
    'Washington Capitals' : '15',
    'Chicago Blackhawks' : '16',
    'Detroit Red Wings' : '17',
    'Nashville Predators' : '18',
    'St. Louis Blues' : '19',
    'Calgary Flames' : '20',
    'Colorado Avalanche' : '21',
    'Edmonton Oilers' : '22',
    'Vancouver Canucks' : '23',
    'Anaheim Ducks' : '24',
    'Dallas Stars' : '25',
    'Los Angeles Kings' : '26',
    'San Jose Sharks' : '28',
    'Columbus Blue Jackets' : '29',
    'Minnesota Wild' : '30',
    'Winnipeg Jets' : '52',
    'Arizona Coyotes' : '53',
    'Vegas Golden Knights' : '54',
		'Seattle Kraken': '55'
}

NHL_TEAM_ID_TO_SHORT_NAME = {
	  1: 'NJ',
    2: 'NYI',
		3: 'NYR',
    4: 'Phi',
    5: 'Pit',
    6: 'Bos',
    7: 'Buf',
    8: 'Mon',
    9: 'Ott',
    10: 'Tor',
    12: 'Car',
    13: 'Fla',
    14: 'TB',
    15: 'Was',
    16: 'Chi',
    17: 'Det',
    18: 'Nsh',
    19: 'StL',
    20: 'Cgy',
    21: 'Col',
    22: 'Edm',
    23: 'Van',
    24: 'Anh',
    25: 'Dal',
    26: 'LA',
    28: 'SJ',
    29: 'Cls',
    30: 'Min',
    52: 'Wpg',
    53: 'Ari',
    54: 'VGK',
		55: 'Sea'
}

# Yahoo endpoints 
YAHOO_BASE_URL = 'https://fantasysports.yahooapis.com/fantasy/v2/'
GET_TOKEN_URL = 'https://api.login.yahoo.com/oauth2/get_token' # used for Oauth

# Yahoo Oauth variables and league data - set from env variables at runtime
client_id = ''
client_secret = ''
redirect_uri = ''
league_key = ''
team_id = ''

# Yahoo Oauth variables set after oauth login
access_token = ''
refresh_token = ''

# Pubnub variables - these are used for chat backend
pubnub_publish_key = ''
pubnub_subscribe_key = ''

# Yahoo stat_id mappings - can comment out ones that are not needed
SKATER_STAT_INDEX = {
	'careerGP' : 'career GP',
	'0' : 'GP',
	'1' : 'G',
	'2' : 'A',
	'3' : 'P',
	'4' : '+/-',
	'5' : 'PIM',
	# '6' : 'PPG',
	# '7' : 'PPA',
	'8' : 'PPP',
	# '9' : 'SHG?',
	# '10' : 'SHA?',
	# '11' : '',
	# '12' : '',
	# '13' : '',
	'14' : 'SOG',
	'15' : 'S%',
	'16' : 'FW',
	# '17' : 'FOL',
	# '18' : 'Starts',
	# '19' : 'W',
	# '20' : '',
	# '21' : '',
	# '22' : 'GA',
	# '23' : 'GAA',
	# '24' : 'SA',
	# '25' : 'SV',
	# '26' : 'SV%',
	# '27' : '',
	# '28' : '',
	# '29' : 'GP?',
	# '30' : 'GP?',
	'31' : 'HIT',
	'32' : 'BLK'
}

GOALIE_STAT_INDEX = {
	'careerGP' : 'career GP',
	'18' : 'GS',
	'19' : 'W',
	# '20' : '',
	# '21' : '',
	'22' : 'GA',
	'23' : 'GAA',
	'24' : 'SA',
	'25' : 'SV',
	'26' : 'SV%',
	# '27' : '',
	# '28' : '',
}
