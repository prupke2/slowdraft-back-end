from app import *
import db
import config

class PostForm(Form):
	title = StringField('Title', [validators.Length(min=1, max=200)])
	body = TextAreaField('Body', [validators.Length(min=1, max=20000)])

def getRules():
	database = db.DB()
	database.cur.execute("SELECT * FROM rules WHERE yahoo_league_id = %s ORDER BY `order`", [session['yahoo_league_id']])
	return database.cur.fetchall()

def newRule(title, body):
	database = db.DB()
	sql = "INSERT INTO rules(title, body, league_id, yahoo_league_id) VALUES(%s, %s, %s, %s)"
	database.cur.execute(sql, (title, body, session['league_id'], session['yahoo_league_id']))
	database.connection.commit()
	return

def editRule(id):
	database = db.DB()
	result = database.cur.execute("SELECT * FROM rules WHERE rule_id=%s", [id])
	if result == 0:
		return redirect(url_for('forum'))
	rule = database.cur.fetchone()
	if rule['yahoo_league_id'] != int(session['yahoo_league_id']):
		flash("Rule does not exist or is not in your league", 'danger')
		return redirect(url_for('rules'))
	return rule	
	
def updateRule(title, body, id):
	database = db.DB()
	sql = "UPDATE rules SET title=%s, body=%s, league_id=%s, yahoo_league_id=%s WHERE rule_id=%s"
	database.cur.execute(sql, (title, body, session['league_id'], session['yahoo_league_id'], id))
	database.connection.commit()

def deleteRule(id):
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
