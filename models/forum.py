from app import * 
import credentials
import datetime
# import yahoo_api
import db
# import download_players
# from models import rules

# class ForumReplyForm(Form):
# 	body = TextAreaField('Body', [validators.Length(min=1, max=20000)])	

def get_forum_posts():
	if 'yahoo_league_id' not in session:
		session['yahoo_league_id'] = credentials.yahoo_league_id
	
	if 'offset' not in session:
		session['offset'] = -5
	sql = ("SELECT f.*, u.username AS 'user', u.role, u.color, u.user_id \
		FROM forum f left join users u on u.yahoo_team_id = f.yahoo_team_id \
		WHERE f.parent_id IS NULL \
		AND f.yahoo_league_id = %s \
		ORDER BY update_date DESC")

	database = db.DB()
	posts = database.fetchAll(sql, session['yahoo_league_id'])
	for post in posts:
		post['create_date'] = post['create_date'] - datetime.timedelta(minutes=int(float(session['offset'])))
		post['update_date'] = post['update_date'] - datetime.timedelta(minutes=int(float(session['offset'])))
	print(str(posts))
	return posts

def getForumPost(id):
	sql = "SELECT * FROM forum WHERE id = %s"	
	database = db.DB()
	database.cur.execute(sql, id)
	return database.cur.fetchone()	

def viewForumPost(id):
	database = db.DB()
	sql = "SELECT * FROM forum f left join users u on u.user_id = f.user_id WHERE id=%s"
	post = database.fetchOne(sql, id)

	if post is None:
		msg = "This post does not exist"
		return msg, '', False
	post['create_date'] = post['create_date'] - datetime.timedelta(minutes=int(float(session['offset'])))
	post['update_date'] = post['update_date'] - datetime.timedelta(minutes=int(float(session['offset'])))
	sql = "SELECT * FROM forum f left join users u on u.user_id = f.user_id WHERE parent_id=%s"
	replies = database.fetchAll(sql, id)
	msg = False
	for reply in replies:
		reply['create_date'] = reply['create_date'] - datetime.timedelta(minutes=int(float(session['offset'])))
		reply['update_date'] = reply['update_date'] - datetime.timedelta(minutes=int(float(session['offset'])))
	return post, replies, msg

def newForumPost(parent_id):
	form = rules.PostForm(request.form)
	title = form.title.data
	body = form.body.data
	time = datetime.datetime.utcnow()

	sql = "INSERT INTO forum(title, body, user_id, league_id, yahoo_league_id, yahoo_team_id, create_date, update_date, parent_id) \
			VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"

	database = db.DB()
	database.cur.execute(sql, (title, body, session['user_id'], session['league_id'], session['yahoo_league_id'], \
		session['team_id'], time, time, parent_id))
	database.connection.commit()
	if parent_id is None:
		msg = "Post created."
		return msg, None
	else:
		updateParentTimestamp(parent_id)
		msg = "Reply posted."	
	return msg, parent_id

def updateForumPost(title, body, id, parent_id):
	database = db.DB()
	sql = "UPDATE forum SET title=%s, body=%s, user_id=%s, update_date = %s WHERE id=%s"
	database.cur.execute(sql, (title, body, session['user_id'], datetime.datetime.utcnow(), id))
	database.connection.commit()
	if parent_id is not None:
		updateParentTimestamp(parent_id)
	database.cur.close()

def updateParentTimestamp(parent_id):
	database = db.DB()
	sql = "UPDATE forum SET update_date=%s WHERE id=%s"
	database.cur.execute(sql, (datetime.datetime.utcnow(), parent_id))
	database.connection.commit()
	database.cur.close()


def deleteForumPost(id):
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
