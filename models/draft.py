from app import *
import db
# from models import players
from models import emails

# Legacy endpoint to avoid interrupting draft for users who don't refresh
def get_dp(draft_id):
	database = db.DB()
	database.cur.execute("SELECT * FROM draft WHERE draft_id = %s", draft_id)
	draft = database.cur.fetchone()
	draft_start_time = draft['draft_start_time_utc']
	sql = "SELECT d.*, u.*, y.player_id, y.name AS player_name, y.prospect, y.careerGP, y.team, y.position \
				 FROM draft_picks d INNER JOIN users u ON u.user_id = d.user_id"
	sql += " LEFT JOIN yahoo_db_21 y ON y.player_id = d.player_id WHERE d.draft_id = %s ORDER BY overall_pick"
	database.cur.execute(sql, draft_id)
	draft_picks = database.cur.fetchall()
	current_pick = get_current_pick_info(draft['current_pick'], draft_id)
	
	# sql = "SELECT * FROM draft_order do INNER JOIN users u ON u.user_id = do.user_id" \
  #                   " WHERE draft_id = %s ORDER BY draft_order"
	# user_count = database.cur.execute(sql, session['draft_id'])
	# users = database.cur.fetchone()
	# users = get_all_users()
	return draft, draft_start_time, draft_picks, current_pick

def get_draft(draft_id, user_id):
	database = db.DB()
	database.cur.execute("SELECT * FROM draft WHERE draft_id = %s", draft_id)
	draft = database.cur.fetchone()
	draft_start_time = draft['draft_start_time_utc']
	# full_draft_date = datetime.datetime.strftime(draft['draft_start_time_utc'], '%A, %b %d, %Y at %I:%M %p')

	sql = "SELECT d.*, u.user_id, u.color, u.username, y.player_id, y.name AS player_name, y.prospect, y.careerGP, y.team, y.position, y.headshot \
		 FROM draft_picks d INNER JOIN users u ON u.user_id = d.user_id"
	sql += " LEFT JOIN yahoo_db_21 y ON y.player_id = d.player_id WHERE d.draft_id = %s ORDER BY overall_pick"
	database.cur.execute(sql, draft_id)
	draft_picks = database.cur.fetchall()
	current_pick = get_current_pick_info(draft['current_pick'], draft_id)

	sql = "SELECT drafting_now FROM users WHERE user_id=%s"
	database.cur.execute(sql, user_id)
	result = database.cur.fetchone()
	drafting_now = result['drafting_now']
	# sql = "SELECT * FROM draft_order do INNER JOIN users u ON u.user_id = do.user_id" \
  #                   " WHERE draft_id = %s ORDER BY draft_order"
	# user_count = database.cur.execute(sql, session['draft_id'])
	# users = database.cur.fetchone()
	# users = get_all_users()
	return draft, drafting_now, draft_start_time, draft_picks, current_pick

def get_all_users():
	database = db.DB()
	sql = "SELECT u.* FROM users u INNER JOIN draft d ON d.league_id = u.league_id \
						  WHERE u.league_id = %s AND d.draft_id=%s"
	database.cur.execute(sql, (session['league_id'], session['draft_id']))
	users = database.cur.fetchall()	
	return users

def change_pick(new_user_id, overall_pick, league_id, draft_id):
	database = db.DB()
	now = datetime.datetime.utcnow()
	database.cur.execute("SELECT * FROM draft_picks dp INNER JOIN users u ON u.user_id = dp.user_id \
					WHERE dp.overall_pick = %s AND draft_id=%s", (overall_pick, draft_id))
	old_user = database.cur.fetchone()
	# flash(str(old_user['drafting_now']), 'success')
	if old_user['drafting_now'] == 1:
		# Make sure this user doesn't have any other active picks before settings drafting_now = 0
		pick_check = database.cur.execute("SELECT * FROM draft_picks WHERE draft_id = %s AND user_id = %s \
				AND pick_expires > %s AND overall_pick != %s AND player_id IS NULL",
					(draft_id, old_user['user_id'], now, overall_pick))
		if pick_check == 0:
			database.cur.execute("UPDATE users SET drafting_now = 0 WHERE user_id = %s", [old_user['user_id']])
			database.connection.commit()

	database.cur.execute("UPDATE draft_picks SET user_id=%s WHERE overall_pick = %s AND draft_id=%s",
				(new_user_id, overall_pick, draft_id))
	database.connection.commit()

	sql = """ UPDATE updates 
		SET latest_draft_update = %s
		WHERE league_id = %s
	"""
	database.cur.execute(sql, (now, league_id))
	database.connection.commit()

	# check if the pick that was changed is the current pick - if it is, let the new user draft 
	database.cur.execute("SELECT * FROM draft WHERE draft_id = %s", draft_id)
	draft = database.cur.fetchone()
	if overall_pick == draft['current_pick']:
		database.cur.execute("UPDATE users SET drafting_now = 1 WHERE user_id = %s", [new_user_id])
		database.connection.commit()
	# database.cur.close()
	return True

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
	sql = """ UPDATE updates 
		SET latest_draft_update = %s
		WHERE league_id = %s
	"""
	database.cur.execute(sql, (now, league_id))
	database.connection.commit()

	if disabled == 1:
		return 'disabled'
	return 'enabled'

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


def make_pick(draft_id, player_id, user_id):
	if check_if_taken(draft_id, player_id) == True:
		return None, None, None

	pick = get_earliest_pick(draft_id, user_id)
	if pick is None:
		return None, None, False
	commit_pick(draft_id, player_id, user_id, pick['overall_pick'])
	nextPick = check_next_pick(draft_id, pick['overall_pick'])
	if nextPick is None:
		set_drafting_now(user_id, 0)
		return None, None, False
	else:
		if user_id != nextPick['user_id']:
			# and (user_id not in (131, 132, 136, 137)):
			draftingAgain = False
			set_drafting_now(user_id, 0)
			set_drafting_now(nextPick['user_id'], 1)
			emails.next_pick_email(nextPick['email'])
		else:
			draftingAgain = True	
	player_data = get_one_player_from_db(player_id)
	print(f"player: {player_data}")
	print(f"nextPick: {nextPick}")
	player = []
	player.extend((player_data['name'], player_data['position'], player_data['team']))
	return player, nextPick, draftingAgain

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

def get_earliest_pick(draft_id, user_id):
	database = db.DB()
	sql = """ SELECT d.*, u.name, u.email
			FROM draft_picks d
			INNER JOIN users u ON u.user_id = d.user_id
			WHERE player_id IS NULL
			AND d.draft_id = %s
			AND d.user_id = %s
			AND d.disabled = 0
			ORDER BY d.overall_pick ASC
		"""
	database.cur.execute(sql, (draft_id, user_id))
	return database.cur.fetchone()

def commit_pick(draft_id, player_id, user_id, pick):
	database = db.DB()
	sql = """ UPDATE draft_picks
			SET player_id = %s, draft_pick_timestamp = %s
			WHERE overall_pick = %s
			AND draft_id = %s
	"""
	now = datetime.datetime.utcnow()
	database.cur.execute(sql, (player_id, now, pick, draft_id))
	database.connection.commit()
	sql = """ INSERT INTO user_team(draft_id, user_id, is_keeper, player_id)
			VALUES (%s, %s, 0, %s)
	"""
	database.cur.execute(sql, (draft_id, user_id, player_id))
	database.connection.commit()
	sql = """ UPDATE updates 
			SET latest_draft_update = %s, latest_team_update = %s, latest_player_db_update = %s, latest_goalie_db_update = %s
			WHERE league_id IN (54, 64)
	"""
	print(f"updating draft, team, db to now: {now}")
	database.cur.execute(sql, (now, now, now, now))
	database.connection.commit()
	return

def check_next_pick(draft_id, pick):
	database = db.DB()
	sql = """ SELECT *
			FROM draft_picks d
			INNER JOIN users u ON u.user_id = d.user_id
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

def set_drafting_now(user_id, value):
	database = db.DB()
	sql = """
		UPDATE users
		SET drafting_now = %s
		WHERE user_id = %s
	"""
	database.cur.execute(sql, (value, user_id))
	database.connection.commit()
	return

def get_current_pick_info(pick, draft_id):
	database = db.DB()
	sql = "SELECT * FROM users u INNER JOIN draft_picks dp ON dp.user_id = u.user_id \
			WHERE dp.overall_pick = %s AND dp.draft_id = %s"

	print(str(sql) + "pick: " + str(pick))
	database.cur.execute(sql, (pick, draft_id))	
	current_pick = database.cur.fetchone()
	print(str(current_pick))
	return current_pick

def check_current_pick_in_draft(draft_id):
	database = db.DB()
	sql = """SELECT *
			FROM draft_picks d
			INNER JOIN users u ON u.user_id = d.user_id
			WHERE draft_id = %s
			AND pick_expires is NOT NULL
			AND player_id IS NULL
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
		database.cur.execute(sql, (current_pick, draft_id))
	database.connection.commit()
	return	
# if session.get('league_id') is None or session['league_id'] == '0':
# 	session['draft_id'] = '0'
# return redirect(url_for('league'))

def add_pick_to_draft(draft_id, league_id, user_id):
	database = db.DB()
	sql = """SELECT MAX(overall_pick) AS 'last_pick'
		FROM draft_picks d
		WHERE draft_id = %s
	"""
	database.cur.execute(sql, draft_id)
	last_pick = database.cur.fetchone()
	new_pick = last_pick['last_pick'] + 1

	sql = f"""
		INSERT INTO draft_picks(user_id, draft_id, round, overall_pick)
		VALUES(%s, %s, %s, %s)
	"""
	database.cur.execute(sql, (user_id, draft_id, 15, new_pick))
	database.connection.commit()

	sql = """ UPDATE updates 
		SET latest_draft_update = %s
		WHERE league_id = %s
	"""
	database.cur.execute(sql, (datetime.datetime.utcnow(), league_id))
	database.connection.commit()
	return True;

# # get all remaining picks
# all_remaining_picks_result = cur.execute(""" SELECT d.*, u.name
# 											FROM draft_picks d
# 											INNER JOIN users u ON u.user_id = d.user_id
# 											WHERE NHLid IS NULL
# 											AND d.draft_id = %s
# 											ORDER BY d.overall_pick ASC
# 										""", [session['draft_id']])

# # check if the draft is over
# if all_remaining_picks_result == 0:
# 	cur.execute("""     UPDATE draft 
# 						SET is_live = 0, is_over = 1
# 						WHERE draft_id=%s
# 						""", [session['draft_id']])
# 	mysql.connection.commit()
# 	return redirect(url_for('draft'))

# all_remaining_picks = cur.fetchall()

# # get users in draft
# cur.execute("SELECT * FROM draft_order do INNER JOIN users u ON u.user_id = do.user_id" \
# 			" WHERE draft_id = %s ORDER BY draft_order", [session['draft_id']])
# users = cur.fetchall()

# # get all the picks
# draft_picks_result = cur.execute("""
# 	SELECT d.*, u.*,
# 	CASE WHEN pdb.First_Name IS NULL THEN gdb.First_Name ELSE pdb.First_Name END AS First_Name, 
# 	CASE WHEN pdb.Last_Name IS NULL THEN gdb.Last_Name ELSE pdb.Last_Name END AS Last_Name
# 	FROM draft_picks d INNER JOIN users u ON d.user_id = u.user_id 
# 	LEFT JOIN goalie_db_18 gdb ON d.NHLid = gdb.NHLid 
# 	LEFT JOIN player_db_18 pdb ON d.NHLid = pdb.NHLid
# 	WHERE d.draft_id = %s ORDER BY d.overall_pick;
# 	""", [session['draft_id']])
# draft_picks = cur.fetchall()

# # get the most recent pick (highest overall_pick value)
# result = cur.execute(""" SELECT d.*, u.name
# 				FROM draft_picks d
# 				INNER JOIN users u ON u.user_id = d.user_id
# 				WHERE NHLid IS NOT NULL
# 				AND d.draft_id = %s
# 				ORDER BY d.overall_pick DESC
# 			""", [session['draft_id']])

# if result > 0:
# 	last_pick_result = cur.fetchone()
# 	last_pick = last_pick_result['draft_pick_timestamp']
# 	last_pick_number = last_pick_result['overall_pick']
# 	pick_expiry_defined = 0
# else:
# 	# no picks made yet
# 	last_pick = draft['draft_start_time_utc']
# 	last_pick_number = 0
# 	pick_expiry = draft_picks[0]['pick_expires']
# 	pick_expiry_defined = 1

# since_last_pick = datetime.datetime.utcnow() - last_pick
# days, seconds = since_last_pick.days, since_last_pick.seconds
# hours_since_last_pick = (days * 24) + (seconds / 3600)
# picks_to_check = int(float(hours_since_last_pick) / float(per_pick))
# msg = "Since last pick: " + str(since_last_pick) + " hours: " + str(hours_since_last_pick) + " picks: " + str(picks_to_check) \
# 	+ " last pick: " + str(last_pick)
# # flash(msg, 'success')

# # if the current pick has expired, update the draft and send notifications
# if picks_to_check > 0:
# 	if current_pick != last_pick_number + picks_to_check + 1:
# 		current_pick = last_pick_number + picks_to_check + 1
# 		cur.execute("UPDATE draft SET current_pick = %s WHERE draft_id=%s", (current_pick, session['draft_id']))
# 		mysql.connection.commit()

# 		cur.execute("SELECT * FROM draft_picks WHERE overall_pick = %s", [current_pick])
# 		current_pick_result = cur.fetchone()
# 		if current_pick_result == 0:
# 			pick_expiry = last_pick + datetime.timedelta(minutes=((picks_to_check + 1) * per_pick))
# 			cur.execute("UPDATE draft_picks SET pick_expires = %s WHERE draft_id = %s AND overall_pick = %s",
# 						(pick_expiry, session['draft_id'], current_pick))
# 			mysql.connection.commit()
# 		# flash(current_pick_result, 'success')

# 		msg = "last pick number: " + str(last_pick_number) + ", current pick: " + str(current_pick) + ", picks to check: " + str(picks_to_check)
# 		# flash(msg, 'success')
# 		#if (int(last_pick_number) + int(picks_to_check) + 1) != int(current_pick):

# 		#current_pick += picks_to_check

# 		# lets other users draft if previous picks' time has elapsed
# 		for count, pick in enumerate(all_remaining_picks, start=1):
# 			time_check = count * per_pick

# 			cur.execute("SELECT * FROM users WHERE user_id = %s", [pick['user_id']])
# 			user_info = cur.fetchone()
# 			msg = str(pick) + " Time check: " + str(time_check) + ", count: " + str(count) \
# 				  + ", drafting_now: " + str(user_info['drafting_now'])
# 			#flash(msg, 'success')

# 			pick_expiry = last_pick + datetime.timedelta(hours=(count * per_pick))
# 			cur.execute("UPDATE draft_picks SET pick_expires = %s WHERE overall_pick = %s AND draft_id = %s",
# 						(pick_expiry, pick['overall_pick'], session['draft_id']))

# 			# if the previous pick has expired, notify the user that it's their turn to draft
# 			if user_info['drafting_now'] == 0:
# 				cur.execute("UPDATE users SET drafting_now = 1 WHERE user_id = %s",
# 											[pick['user_id']])

# 				NextPickEmail(user_info['name'], user_info['email'])
# 				if user_info['phone_number'] is not None:
# 					phone = "+1" + str(user_info['phone_number'])
# 					NextPickSMS(user_info['name'], phone)
# 			current_pick_user_id = pick['user_id']
# 			mysql.connection.commit()
# 			if pick['overall_pick'] == (current_pick):

# 				# if current_pick != draft['current_pick']:
# 				#     cur.execute("UPDATE draft SET current_pick = %s WHERE draft_id = %s",
# 				#                     (current_pick, session['draft_id']))
# 				#     mysql.connection.commit()
# 				break
# 		# return redirect(url_for('draft'))

# result = cur.execute("""
# 				SELECT * 
# 				FROM draft_picks dp 
# 				INNER JOIN users u ON u.user_id = dp.user_id 
# 				WHERE dp.draft_id = %s
# 				AND overall_pick=%s
# 				""", (session['draft_id'], current_pick))
# if result > 0:
# 	current_pick_result = cur.fetchone()
# else:

# 	cur.execute("UPDATE draft_picks SET pick_expires = %s WHERE draft_id = %s AND overall_pick = 1",
# 				(last_pick + datetime.timedelta(hours=draft['per_pick']), session['draft_id']))
# 	mysql.connection.commit()
# 	cur.execute("""SELECT * 
# 				FROM draft_picks dp
# 				INNER JOIN users u ON u.user_id = dp.user_id 
# 				WHERE overall_pick = 1 
# 				AND draft_id = %s
# 				""", [session['draft_id']])
# 	current_pick_result = cur.fetchone()


# current_round = "round-" + str(current_pick_result['round'])
# current_pick_user = current_pick_result['username']
# #current_pick_user.replace(' ', '&nbsp;')
# color = current_pick_result['color']
# role = current_pick_result['role']
# # flash(str(current_pick), 'success')

# # pick_expiry = last_pick + datetime.timedelta(hours=(picks_to_check + 1) * per_pick) - datetime.timedelta(minutes=float(session['offset']))

# if pick_expiry_defined == 0:
# 	pick_expiry = current_pick_result['pick_expires'] - datetime.timedelta(minutes=float(session['offset']))
# # flash(pick_expiry, 'success')

# return render_template('draft.html', league=league, draft=draft, draft_picks=draft_picks, users=users,
# 						user_count=user_count, current_pick_user=current_pick_user, color=color, role=role,
# 						pick_expiry=pick_expiry, current_round=current_round, current_pick=current_pick)
# else:

# # draft_picks_result = cur.execute("SELECT * FROM draft_picks d INNER JOIN users u ON d.user_id = u.user_id WHERE draft_id = %s ORDER by d.overall_pick", [session['draft_id']])
# draft_picks_result = cur.execute("""
# 			   SELECT d.*, u.*,
# 			   CASE WHEN pdb.First_Name IS NULL THEN gdb.First_Name ELSE pdb.First_Name END AS First_Name, 
# 			   CASE WHEN pdb.Last_Name IS NULL THEN gdb.Last_Name ELSE pdb.Last_Name END AS Last_Name
# 			   FROM draft_picks d INNER JOIN users u ON d.user_id = u.user_id 
# 			   LEFT JOIN goalie_db_18 gdb ON d.NHLid = gdb.NHLid LEFT JOIN player_db_18 pdb ON d.NHLid = pdb.NHLid
# 			   WHERE d.draft_id = %s ORDER BY d.overall_pick;
# 			   """, [session['draft_id']])
# draft_picks = cur.fetchall()
# current_time = datetime.datetime.utcnow()

# cur.execute("SELECT * FROM draft_order do INNER JOIN users u ON u.user_id = do.user_id" \
# 			" WHERE draft_id = %s ORDER BY draft_order", [session['draft_id']])
# users = cur.fetchall()

# # if no live drafts, check if there is an upcoming draft
# draft_result = cur.execute("SELECT * FROM draft WHERE is_over = 0 and league_id = %s", [session['league_id']])

# if draft_result > 0:
# 	draft = cur.fetchone()
# 	draft_start_time = draft['draft_start_time_utc']
# 	full_draft_date = datetime.datetime.strftime(draft['draft_start_time_utc'], '%A, %b %d, %Y at %I:%M %p')
# 	draft_id = draft['draft_id']
# 	session['draft_id'] = draft_id

# 	# check to see if this draft has actually started already - if it has, set draft.is_live = 1
# 	if draft_start_time < current_time:
# 		drafting_now = cur.fetchone()
# 		user_drafting = draft_picks[0]['user_id']
# 		cur.execute("""
# 			UPDATE draft 
# 			SET is_live = 1
# 			WHERE draft_id=%s
# 			""", [draft_id])
# 		mysql.connection.commit()
# 		cur.execute("UPDATE draft SET current_pick = 1")
# 		cur.execute("SELECT * FROM draft WHERE draft_id=%s", [draft_id])
# 		draft = cur.fetchone()
# 		cur.execute("""
# 			UPDATE users 
# 			SET drafting_now = 1
# 			WHERE user_id=%s
# 			""", [user_drafting])
# 		mysql.connection.commit()
# 		cur.close()
# 		return redirect(url_for('draft'))
# 	else:
# 		cur.close()
# 		# the draft hasn't started yet, so get the time until the draft starts
# 		draft_start_time = str(draft_start_time)
# 		# this erases the microseconds
# 		draft_start_time = draft_start_time[:-7]

# 		return render_template('draft.html', league=league, draft=draft, full_draft_date=full_draft_date,
# 							   draft_picks = draft_picks, user_count=user_count, users=users)
# else:
# 	# no live drafts and no upcoming drafts - see if there is a draft that has finished
# 	draft_result = cur.execute("SELECT * FROM draft WHERE is_over = 1 and league_id = %s \
# 								ORDER BY draft_start_time_utc DESC",
# 							   [session['league_id']])
# 	if draft_result > 0:
# 		draft = cur.fetchone()
# 		session['draft_id'] = draft['draft_id']
# 		draft_picks_result = cur.execute("""
# 						SELECT d.*, u.*,
# 						CASE WHEN pdb.First_Name IS NULL THEN gdb.First_Name ELSE pdb.First_Name END AS First_Name, 
# 						CASE WHEN pdb.Last_Name IS NULL THEN gdb.Last_Name ELSE pdb.Last_Name END AS Last_Name
# 						FROM draft_picks d INNER JOIN users u ON d.user_id = u.user_id 
# 						LEFT JOIN goalie_db_18 gdb ON d.NHLid = gdb.NHLid LEFT JOIN player_db_18 pdb ON d.NHLid = pdb.NHLid
# 						WHERE d.draft_id = %s ORDER BY d.overall_pick;
# 						""", [draft['draft_id']])
# 		draft_picks = cur.fetchall()
# 		is_over = 1
# 		return render_template('draft.html', league=league, draft=draft, draft_picks=draft_picks,
# 							   user_count=user_count, users=users, is_over=is_over)

# 	# no drafts exist in this league
# 	else:

# 		nodraft = 1
# 		session['draft_id'] = '0'
# 		return render_template('draft.html', league=league, nodraft=nodraft)

