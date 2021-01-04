from app import *
import db
import config

def get_rules(league_id):
	database = db.DB()
	database.cur.execute("SELECT * FROM rules WHERE league_id = %s ORDER BY `order`", [league_id])
	return database.cur.fetchall()

def new_rule(post):
	database = db.DB()
	sql = "INSERT INTO rules(title, body, league_id, yahoo_league_id) VALUES(%s, %s, %s, %s)"
	print(f"sql: {sql}")
	database.cur.execute(sql, (post['title'], post['body'], session['league_id'], session['yahoo_league_id']))
	database.connection.commit()
	
	sql = """ UPDATE updates 
			SET latest_rules_update = %s 
			WHERE league_id = %s
	"""
	database.cur.execute(sql, (datetime.datetime.utcnow(), session['league_id']))
	database.connection.commit()
	return

def edit_rule(id):
	database = db.DB()
	result = database.cur.execute("SELECT * FROM rules WHERE rule_id=%s", [id])
	if result == 0:
		return redirect(url_for('forum'))
	rule = database.cur.fetchone()
	if rule['yahoo_league_id'] != int(session['yahoo_league_id']):
		flash("Rule does not exist or is not in your league", 'danger')
		return redirect(url_for('rules'))
	return rule	
	
def update_rule(title, body, id):
	database = db.DB()
	sql = "UPDATE rules SET title=%s, body=%s, league_id=%s, yahoo_league_id=%s WHERE rule_id=%s"
	database.cur.execute(sql, (title, body, session['league_id'], session['yahoo_league_id'], id))
	database.connection.commit()

def delete_rule(id):
	database = db.DB()
	database.cur.execute("SELECT * FROM rules WHERE rule_id=%s", [id])
	rule = database.cur.fetchone()
	# print("\n\nRULE: " + str(rule))
	if rule['yahoo_league_id'] != int(session['yahoo_league_id']):
		return redirect(url_for('rules'))
	database.cur.execute("DELETE FROM rules where rule_id=%s", [id])
	database.connection.commit()
	database.cur.close()
	flash('Rule deleted', 'success')	
