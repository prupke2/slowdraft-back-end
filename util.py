from flask import jsonify

def return_error(message, status = 400):
  return jsonify(
    {
      "success": False,
      "error": message,
      "status": status
    }
  )
