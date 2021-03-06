from app import * 
import datetime
# import yahoo_api
import db
# import download_players
# from models import rules

# class ForumReplyForm(Form):
# 	body = TextAreaField('Body', [validators.Length(min=1, max=20000)])	

def get_forum_posts(league_id):
	# if 'yahoo_league_id' not in session:
	# 	session['yahoo_league_id'] = config.yahoo_league_id
	
	# if 'offset' not in session:
	# 	session['offset'] = -5
	
	sql = ("SELECT f.*, u.username AS 'user', u.role, u.color, u.user_id \
		FROM forum f INNER JOIN users u on u.league_id = f.league_id \
		WHERE f.parent_id IS NULL \
		AND f.league_id = %s \
		AND f.user_id = u.user_id \
		ORDER BY update_date DESC")

	database = db.DB()
	posts = database.fetchAll(sql, [league_id])
	for post in posts:
		post['create_date'] = post['create_date'] - datetime.timedelta(minutes=int(float(0)))
		post['update_date'] = post['update_date'] - datetime.timedelta(minutes=int(float(0)))
	# print(str(posts))
	return posts

def get_forum_post(id):
	sql = "SELECT * FROM forum WHERE id = %s"	
	database = db.DB()
	database.cur.execute(sql, id)
	return database.cur.fetchone()	

def view_post_replies(id):
	database = db.DB()
	sql = "SELECT * FROM forum f left join users u on u.user_id = f.user_id WHERE id=%s"
	post = database.fetchOne(sql, id)

	if post is None:
		msg = "This post does not exist"
		return None
	post['create_date'] = post['create_date'] - datetime.timedelta(minutes=int(float(session['offset'])))
	post['update_date'] = post['update_date'] - datetime.timedelta(minutes=int(float(session['offset'])))
	sql = "SELECT * FROM forum f left join users u on u.user_id = f.user_id WHERE parent_id=%s"
	# print(f"sql: {sql}")
	replies = database.fetchAll(sql, id)
	msg = False
	for reply in replies:
		reply['create_date'] = reply['create_date'] - datetime.timedelta(minutes=int(float(session['offset'])))
		reply['update_date'] = reply['update_date'] - datetime.timedelta(minutes=int(float(session['offset'])))
	return replies

def new_forum_post(post):
	print("In forum.new_forum_post")
	now = datetime.datetime.utcnow()

	sql = "INSERT INTO forum(title, body, user_id, league_id, yahoo_league_id, yahoo_team_id, create_date, update_date, parent_id) \
			VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"

	database = db.DB()
	database.cur.execute(sql, (post['title'], post['body'], session['user_id'], session['league_id'], session['yahoo_league_id'], \
		session['team_id'], now, now, post['parentId']))
	database.connection.commit()
	sql = """ UPDATE updates 
			SET latest_forum_update = %s 
			WHERE league_id = %s
	"""
	database.cur.execute(sql, (now, session['league_id']))
	database.connection.commit()
	return

def update_forum_post(title, body, id, parent_id):
	database = db.DB()
	sql = "UPDATE forum SET title=%s, body=%s, user_id=%s, update_date = %s WHERE id=%s"
	database.cur.execute(sql, (title, body, session['user_id'], datetime.datetime.utcnow(), id))
	database.connection.commit()
	if parent_id is not None:
		update_parent_timestamp(parent_id)
	database.cur.close()

def update_parent_timestamp(parent_id):
	database = db.DB()
	sql = "UPDATE forum SET update_date=%s WHERE id=%s"
	database.cur.execute(sql, (datetime.datetime.utcnow(), parent_id))
	database.connection.commit()
	database.cur.close()

def delete_forum_post(id):
	sql = "SELECT user_id FROM forum WHERE id=%s"
	database = db.DB()
	database.cur.execute(sql, id)
	user_check = database.cur.fetchone()
	user = int(user_check['user_id'])
	if user != int(session['user_id']):
		return False
	sql = "DELETE FROM forum where id=%s"
	database.cur.execute(sql, id)	
	database.connection.commit()
	database.cur.close()
	return True   
