from app import *
from db import *

def getNHLId(name):
	NHL_PLAYER_SEARCH_URL = "https://suggest.svc.nhl.com/svc/suggest/v1/min_all/" + name + "/1"
	response = requests.get(NHL_PLAYER_SEARCH_URL)
	if response.status_code >= 200 and response.status_code <= 203:
		result=response.json()
		if result['suggestions'] != []:
			return result['suggestions'][0][2:9]
		else:
			return 0	
	else:
		print("There was an error hitting NHL API: \n\n" + str(response.status_code) + " " + str(response.json))
		return 0	

def getCareerGamesPlayed(id):
	NHL_PLAYER_INFO_URL = "https://statsapi.web.nhl.com/api/v1/people/" + str(id) + "?expand=person.stats&stats=careerRegularSeason"		
	response = requests.get(NHL_PLAYER_INFO_URL)
	if response.status_code >= 200 and response.status_code <= 203:
		result=response.json()
		if result['people'][0]['stats'][0]['splits'] == []:
			return 0
		else:
			return result['people'][0]['stats'][0]['splits'][0]['stat']['games']

