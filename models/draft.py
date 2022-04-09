from app import *
import db
from models import emails

def get_draft(draft_id, team_key):
	database = db.DB()
	database.cur.execute("SELECT * FROM draft WHERE draft_id = %s", draft_id)
	draft = database.cur.fetchone()

	sql = """
			SELECT d.*, u.yahoo_team_id, u.color, u.username, y.player_id, y.name AS player_name, y.prospect, y.careerGP, y.team, y.position, y.headshot
			FROM draft_picks d 
			INNER JOIN users u 
				ON u.team_key = d.team_key
		 	LEFT JOIN yahoo_db_21 y 
				ON y.player_id = d.player_id 
			WHERE d.draft_id = %s 
			ORDER BY overall_pick
		"""
	database.cur.execute(sql, draft_id)
	draft_picks = database.cur.fetchall()
	current_pick = get_current_pick_info(draft['current_pick'], draft_id)

	database.cur.execute("SELECT drafting_now FROM users WHERE team_key=%s", team_key)
	result = database.cur.fetchone()
	drafting_now = False
	if result['drafting_now'] == 1:
		drafting_now = True

	return jsonify({
		'draft': draft, 
		'drafting_now': drafting_now, 
		'picks': draft_picks, 
		'current_pick': current_pick
	})

def get_all_users():
	database = db.DB()
	sql = "SELECT u.* FROM users u INNER JOIN draft d ON d.league_id = u.league_id \
						  WHERE u.league_id = %s AND d.draft_id=%s"
	database.cur.execute(sql, (session['league_id'], session['draft_id']))
	users = database.cur.fetchall()	
	return users

def change_pick(team_key, overall_pick, yahoo_league_id, draft_id):
	database = db.DB()
	now = datetime.datetime.utcnow()
	database.cur.execute("SELECT * FROM draft_picks dp INNER JOIN users u ON u.team_key = dp.team_key \
					WHERE dp.overall_pick = %s AND draft_id=%s", (overall_pick, draft_id))
	old_user = database.cur.fetchone()
	if old_user['drafting_now'] == 1:
		# Make sure this user doesn't have any other active picks before settings drafting_now = 0
		pick_check = database.cur.execute("SELECT * FROM draft_picks WHERE draft_id = %s AND team_key = %s \
				AND pick_expires > %s AND overall_pick != %s AND player_id IS NULL",
					(draft_id, old_user['team_key'], now, overall_pick))
		if pick_check == 0:
			database.cur.execute("UPDATE users SET drafting_now = 0 WHERE team_key = %s", [old_user['team_key']])
			database.connection.commit()

	database.cur.execute("UPDATE draft_picks SET team_key=%s WHERE overall_pick = %s AND draft_id=%s",
				(team_key, overall_pick, draft_id))
	database.connection.commit()

	util.update('latest_draft_update', draft_id)

	# check if the pick that was changed is the current pick - if it is, let the new user draft 
	database.cur.execute("SELECT * FROM draft WHERE draft_id = %s", draft_id)
	draft = database.cur.fetchone()
	if overall_pick == draft['current_pick']:
		database.cur.execute("UPDATE users SET drafting_now = 1 WHERE team_key = %s", [team_key])
		database.connection.commit()
	return util.return_true()

def toggle_pick_enabled(overall_pick, league_id, draft_id):
	database = db.DB()
	now = datetime.datetime.utcnow()
	disabled = 1
	database.cur.execute("SELECT disabled FROM draft_picks WHERE overall_pick = %s AND draft_id=%s",
				(overall_pick, draft_id))	
	pick = database.cur.fetchone()
	if pick['disabled'] == 1:
		disabled = 0
	database.cur.execute("UPDATE draft_picks SET disabled=%s WHERE overall_pick = %s AND draft_id=%s",
				(disabled, overall_pick, draft_id))
	database.connection.commit()

	# in case the current pick has just been disabled
	check_current_pick_in_draft(draft_id)
	util.update('latest_draft_update', draft_id)

	new_status = 'disabled' if disabled == 1 else 'enabled'
	return jsonify({'success': True, 'status': new_status})

def set_draft_picks(rounds, snake):
	overall_pick_count = 1
	database = db.DB()
	sql = "SELECT * FROM draft_order d INNER JOIN users u ON d.user_id = u.user_id WHERE d.draft_id = %s ORDER BY draft_order"
	user_count = database.cur.execute(sql, session['draft_id'])
	users = database.cur.fetchall()
	print("Setting picks...\n")
	for round in range(1, int(rounds) + 1):
		if snake == True:
			if (round > 1):
				# since the snake draft starts at the end of the round, this jumps it up a round
				overall_pick_count += user_count
				if round % 2 == 0:
					overall_pick_count -=1
				else:
					overall_pick_count +=1
		for user in users:
			sql = "INSERT INTO draft_picks(draft_id, user_id, overall_pick, round) VALUES(%s, %s, %s, %s)"
			database.cur.execute(sql, (session['draft_id'], user['user_id'], overall_pick_count, round))
			database.connection.commit()
			if (snake == True) and (round % 2 == 0):
				overall_pick_count -= 1
			else:
				if round == 1 and overall_pick_count == 12:
					overall_pick_count += 1
					database.cur.execute(sql, (session['draft_id'], 411, overall_pick_count, round))
					database.connection.commit()
				overall_pick_count += 1


def make_pick(draft_id, player_id, team_key):
	if check_if_taken(draft_id, player_id) == True:
		return return_error('already_drafted')
	pick = get_earliest_pick(draft_id, team_key)
	if pick is None:
		return return_error('no_remaining_picks')
	commit_pick(draft_id, player_id, team_key, pick['overall_pick'])
	next_pick = check_next_pick(draft_id, pick['overall_pick'])
	if next_pick is None:
		set_drafting_now(team_key, 0)
		return jsonify({
			"success": True, 
			"player": None, 
			"next_pick": None, 
			"drafting_again": False
		})
	if team_key == next_pick['team_key']:
		drafting_again = True
	else:
		drafting_again = False
		set_drafting_now(team_key, 0)
		set_drafting_now(next_pick['team_key'], 1)
		emails.next_pick_email(next_pick['email'])
	player_data = get_one_player_from_db(player_id)
	player = []
	player.extend((player_data['name'], ' ' + player_data['position'], ' ' + player_data['team']))
	return jsonify({'success': True, 'player': player, 'next_pick': next_pick, 'drafting_again': drafting_again})

def check_if_taken(draft_id, player_id):
	database = db.DB()
	sql = "SELECT player_id FROM user_team WHERE draft_id = %s AND player_id = %s"
	database.cur.execute(sql, (draft_id, player_id))
	result = database.cur.fetchone()
	print(f"result: {result}")
	if result is None:
		return False
	return True

def get_one_player_from_db(player_id):
	database = db.DB()
	sql = "SELECT * FROM yahoo_db_21 WHERE player_id = %s"
	database.cur.execute(sql, player_id)
	return database.cur.fetchone()	

def get_earliest_pick(draft_id, team_key):
	database = db.DB()
	sql = """ SELECT d.*, u.name, u.email
			FROM draft_picks d
			INNER JOIN users u ON u.team_key = d.team_key
			WHERE player_id IS NULL
			AND d.draft_id = %s
			AND d.team_key = %s
			AND d.disabled = 0
			ORDER BY d.overall_pick ASC
		"""
	database.cur.execute(sql, (draft_id, team_key))
	return database.cur.fetchone()

def commit_pick(draft_id, player_id, team_key, pick):
	database = db.DB()
	sql = """ UPDATE draft_picks
			SET player_id = %s, draft_pick_timestamp = %s
			WHERE overall_pick = %s
			AND draft_id = %s
	"""
	now = datetime.datetime.utcnow()
	database.cur.execute(sql, (player_id, now, pick, draft_id))
	database.connection.commit()
	sql = """ INSERT INTO user_team(draft_id, team_key, is_keeper, player_id)
			VALUES (%s, %s, 0, %s)
	"""
	database.cur.execute(sql, (draft_id, team_key, player_id))
	database.connection.commit()
	sql = """ UPDATE updates 
			SET latest_draft_update = %s, latest_team_update = %s, latest_player_db_update = %s, latest_goalie_db_update = %s
			WHERE draft_id = %s
	"""
	print(f"updating draft, team, db to now: {now}")
	database.cur.execute(sql, (now, now, now, now, draft_id))
	database.connection.commit()
	return util.return_true()

def check_next_pick(draft_id, pick):
	database = db.DB()
	sql = """ SELECT *
			FROM draft_picks d
			INNER JOIN users u ON u.team_key = d.team_key
			WHERE draft_id = %s
			AND overall_pick > %s
			AND disabled = 0
			ORDER BY overall_pick
		"""
	remainingPicks = database.cur.execute(sql, (draft_id, pick))
	nextPick = database.cur.fetchone()
	if nextPick is None:
		print("nextPick is none")
		check_current_pick_in_draft(draft_id)
	else:	
		print("Next pick: " + str(nextPick))
		if nextPick['pick_expires'] is None:
			sql = "UPDATE draft_picks d SET pick_expires = %s WHERE draft_pick_id = %s"
			now = datetime.datetime.utcnow()
			current_hour_utc = now.strftime("%H")

			# if the pick is made overnight (10pm to 9am ET), set the new pick expiry to the next day at 1pm ET
			if 2 <= int(current_hour_utc) < 13:
				pick_expiry = datetime.datetime(now.year, now.month, now.day, 17, 0, 0)
			else:
				pick_expiry = datetime.datetime.utcnow() + datetime.timedelta(hours = 4)
			database.cur.execute(sql, (pick_expiry, nextPick['draft_pick_id']))
			database.connection.commit()
			sql = "UPDATE draft SET current_pick=%s WHERE draft_id=%s"
			print("Query 2: " + str(sql))
			database.cur.execute(sql, (nextPick['overall_pick'], draft_id))
			database.connection.commit()
	return nextPick

def set_drafting_now(team_key, value):
	database = db.DB()
	sql = """
		UPDATE users
		SET drafting_now = %s
		WHERE team_key = %s
	"""
	database.cur.execute(sql, (value, team_key))
	database.connection.commit()
	return

def get_current_pick_info(pick, draft_id):
	database = db.DB()
	sql = "SELECT * FROM users u INNER JOIN draft_picks dp ON dp.team_key = u.team_key \
			WHERE dp.overall_pick = %s AND dp.draft_id = %s"

	database.cur.execute(sql, (pick, draft_id))	
	current_pick = database.cur.fetchone()
	return current_pick

def check_current_pick_in_draft(draft_id):
	database = db.DB()
	sql = """SELECT *
			FROM draft_picks d
			INNER JOIN users u ON u.team_key = d.team_key
			WHERE draft_id = %s
			AND pick_expires is NOT NULL
			AND player_id IS NULL
			AND disabled = 0
			ORDER BY overall_pick DESC
		"""
	database.cur.execute(sql, draft_id)
	current_pick = database.cur.fetchone()
	print("current: " + str(current_pick))
	if current_pick is None:
		sql = "UPDATE draft SET is_live=%s, is_over=%s WHERE draft_id=%s"
		database.cur.execute(sql, (0, 1, draft_id))
	else:
		sql = "UPDATE draft SET current_pick=%s WHERE draft_id=%s"
		pick = current_pick['overall_pick']
		print(f"pick: {pick}")
		database.cur.execute(sql, (pick, draft_id))
	database.connection.commit()
	return	

def add_pick_to_draft(draft_id, yahoo_league_id, team_key):
	database = db.DB()
	sql = """SELECT MAX(overall_pick) AS 'last_pick'
		FROM draft_picks d
		WHERE draft_id = %s
	"""
	database.cur.execute(sql, draft_id)
	last_pick = database.cur.fetchone()
	new_pick = last_pick['last_pick'] + 1
	sql = f"""
		INSERT INTO draft_picks(draft_id, round, overall_pick, team_key)
		VALUES(%s, %s, %s, %s)
	"""
	database.cur.execute(sql, (draft_id, 15, new_pick, team_key))
	database.connection.commit()

	util.update('latest_draft_update', draft_id)
	return util.return_true()
