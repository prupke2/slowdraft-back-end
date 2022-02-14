from app import * 
import datetime
import db
from util import return_error
from flask import jsonify

def get_forum_posts(yahoo_league_id):	
	sql = ("SELECT f.*, u.username AS 'user', u.role, u.color, u.yahoo_team_id \
		FROM forum f INNER JOIN users u on u.yahoo_league_id = f.yahoo_league_id \
		WHERE f.parent_id IS NULL \
		AND f.yahoo_league_id = %s \
		AND f.team_key = u.team_key \
		ORDER BY update_date DESC")

	database = db.DB()
	posts = database.fetchAll(sql, [yahoo_league_id])
	for post in posts:
		post['create_date'] = post['create_date'] - datetime.timedelta(minutes=int(float(0)))
		post['update_date'] = post['update_date'] - datetime.timedelta(minutes=int(float(0)))
	return jsonify({'success': True, 'posts': posts})

def get_forum_post(id):
	sql = "SELECT * FROM forum WHERE id = %s"	
	database = db.DB()
	database.cur.execute(sql, id)
	return jsonify({'success': True, 'post': database.cur.fetchone()})

def get_post_replies(yahoo_league_id, post_id):
	database = db.DB()
	sql = """
		SELECT f.create_date, f.update_date, f.body, f.title, u.yahoo_team_id, u.username
		FROM forum f 
		LEFT JOIN users u 
		ON u.team_key = f.team_key 
		WHERE f.yahoo_league_id=%s
		AND f.parent_id=%s
		 
	"""
	replies = database.fetchAll(sql, (yahoo_league_id, post_id))
	if replies is False:
		replies = []
	else:
		for reply in replies:
			reply['create_date'] = reply['create_date'] - datetime.timedelta(minutes=int(float(0)))
			reply['update_date'] = reply['update_date'] - datetime.timedelta(minutes=int(float(0)))
	return jsonify({"success": True, 	"replies": replies })

def new_forum_post(post, user):
	now = datetime.datetime.utcnow()
	print(f"user: {user}")
	sql = "INSERT INTO forum(title, body, team_key, yahoo_league_id, create_date, update_date, parent_id, yahoo_team_id) \
			VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"

	database = db.DB()
	database.cur.execute(sql, (post['title'], post['body'], user['team_key'], user['yahoo_league_id'], \
		now, now, post['parentId'], user['yahoo_team_id']))
	database.connection.commit()
	util.update('latest_forum_update', user['draft_id'])

	if post['parentId'] is not None:
		update_parent_timestamp(post['parentId'])
	return util.return_true()

def update_forum_post(user, title, body, id, parent_id):
	database = db.DB()
	sql = "UPDATE forum SET title=%s, body=%s, update_date = %s WHERE id=%s"
	database.cur.execute(sql, (title, body, datetime.datetime.utcnow(), id))
	database.connection.commit()
	if parent_id is not None:
		update_parent_timestamp(parent_id)
	return util.return_true()

def update_parent_timestamp(parent_id):
	database = db.DB()
	sql = "UPDATE forum SET update_date=%s WHERE id=%s"
	database.cur.execute(sql, (datetime.datetime.utcnow(), parent_id))
	database.connection.commit()
	return util.return_true()

def delete_forum_post(id):
	database = db.DB()
	sql = "DELETE FROM forum where id=%s"
	database.cur.execute(sql, id)	
	database.connection.commit()
	return util.return_true()   
