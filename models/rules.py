from app import *
import db
import config

def get_rules(yahoo_league_id):
	database = db.DB()
	database.cur.execute("SELECT * FROM rules WHERE yahoo_league_id = %s ORDER BY `order`", [yahoo_league_id])
	return jsonify({'success': True, 'rules': database.cur.fetchall()})

def new_rule(post, user):
	try:
		database = db.DB()
		sql = "INSERT INTO rules(title, body, yahoo_league_id) VALUES(%s, %s, %s)"
		print(f"sql: {sql}")
		database.cur.execute(sql, (post['title'], post['body'], user['yahoo_league_id']))
		database.connection.commit()
		
		util.update('latest_rules_update', user['draft_id'])
		return util.return_true()
	except Exception as e:
		print(f"Error creating rule: {e}")
		return util.return_error('')
	
def update_rule(post, user):
	database = db.DB()
	sql = """
		UPDATE rules
		SET title=%s, body=%s 
		WHERE yahoo_league_id=%s 
		AND rule_id=%s
	"""
	database.cur.execute(sql, (post['title'], post['body'], user['yahoo_league_id'], post['id']))
	database.connection.commit()
	return util.return_true()

def delete_rule(id):
	database = db.DB()
	database.cur.execute("SELECT * FROM rules WHERE rule_id=%s", [id])
	rule = database.cur.fetchone()
	database.cur.execute("DELETE FROM rules where rule_id=%s", [id])
	database.connection.commit()
