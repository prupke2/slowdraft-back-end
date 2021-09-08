from app import *
from config import *
from db import *

def getWatchlist():
	database = db.DB()
	sql = "SELECT DISTINCT w.player_id, y.* FROM watchlist w INNER JOIN yahoo_db_21 y ON y.player_id = w.player_id \
			WHERE yahoo_league_id = %s AND user_id = %s"
	database.cur.execute(sql, (session['yahoo_league_id'], session['user_id']))
	players = database.cur.fetchall()
	skaters = []
	goalies = []
	for player in players:
		if player['position'] == "G":
			goalies.append(player)
		else:
			skaters.append(player)
			
	return skaters, goalies

def getWatchlistIds():
	database = db.DB()
	sql = "SELECT w.player_id FROM watchlist w INNER JOIN yahoo_db_21 y ON y.player_id = w.player_id WHERE yahoo_league_id = %s AND user_id = %s"
	database.cur.execute(sql, (session['yahoo_league_id'], session['user_id']))
	players = database.cur.fetchall()
	print("\n\nPlayers: " + str(players))
	watchlist = []
	for player in players:
		watchlist.append(player['player_id'])
		
	return watchlist

def addToWatchlist(id):
	database = db.DB()
	sql = "INSERT INTO watchlist(yahoo_league_id, user_id, player_id) VALUES(%s, %s, %s)"
	print(sql)
	database.cur.execute(sql, (session['yahoo_league_id'], session['user_id'], id))
	database.connection.commit()
	# return True

def removeFromWatchlist(id):
	database = db.DB()
	sql = "DELETE FROM watchlist WHERE yahoo_league_id = %s AND user_id = %s AND player_id = %s"
	print(sql)
	database.cur.execute(sql, (session['yahoo_league_id'], session['user_id'], id))
	database.connection.commit()
