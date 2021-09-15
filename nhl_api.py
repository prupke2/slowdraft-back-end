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
	NHL_PLAYER_INFO_URL = f"https://statsapi.web.nhl.com/api/v1/people/{str(id)}?expand=person.stats&stats=careerRegularSeason"		
	response = requests.get(NHL_PLAYER_INFO_URL)
	if response.status_code >= 200 and response.status_code <= 203:
		result=response.json()
		if result['people'][0]['stats'][0]['splits'] == []:
			return 0
		else:
			return result['people'][0]['stats'][0]['splits'][0]['stat']['games']

def getNhlDraftRound(year, round):
	NHL_DRAFT_YEAR_URL = f"https://statsapi.web.nhl.com/api/v1/draft/{year}"
	response = requests.get(NHL_DRAFT_YEAR_URL)
	if response.status_code >= 200 and response.status_code <= 203:
		result=response.json()
		return result['drafts'][0]['rounds'][round - 1]['picks']
	else:
		print(f"Error getting draft for year {year}, round {round}. Response: {response}")
		return null

def getNhlProspect(prospect_url):
	NHL_PROSPECT_URL = f"https://statsapi.web.nhl.com{prospect_url}"
	print(f"NHL_PROSPECT_URL: {NHL_PROSPECT_URL}")
	response = requests.get(NHL_PROSPECT_URL)
	if response.status_code >= 200 and response.status_code <= 203:
		result=response.json()
		return result['prospects'][0]
	else:
		print(f"Error getting prospect with url: {prospect_url}. Response: {response}")
		return null
