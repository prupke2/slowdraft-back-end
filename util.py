from flask import jsonify
import db
import datetime

def return_true():
  return jsonify({ "success": True })

def return_error(message, status = 400):
  return jsonify(
    {
      "success": False,
      "error": message,
      "status": status
    }
  )

def update(table, draft_id):
  database = db.DB()
  query = f""" UPDATE updates 
		SET {table} = %s
		WHERE draft_id = %s
	"""
  database.cur.execute(query, (datetime.datetime.utcnow(), draft_id))
  database.connection.commit()
  return

def get_last_row_inserted(table, column):
  database = db.DB()
  database.cur.execute(f"SELECT MAX({column}) FROM {table};")
  max = database.cur.fetchone()
  return max[f'MAX({column})']
