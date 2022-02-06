import datetime
import config
import jwt
from flask import request, jsonify
from functools import wraps
import util

def generate_web_token(my_team, access_token, refresh_token):
  # 3888000 seconds = 45 days
  expiry = datetime.datetime.now() + datetime.timedelta(seconds=3888000)
  payload = {
    "iss": "SlowDraft",
    "access_token": access_token,
    "refresh_token": refresh_token,
    "exp": expiry,
    "draft_id": my_team['draft_id'],
    "yahoo_league_id": my_team['yahoo_league_id'],
    "role": my_team['role'],
    "team_key": my_team['team_key'],
    "team_name": my_team['team_name'],
    "color": my_team['color']
  }
  return jwt.encode(payload, config.client_secret, algorithm="HS256")

def decode_web_token(token):
  return jwt.decode(token, config.client_secret, issuer="SlowDraft", algorithms="HS256")

def exception_handler(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    try:
      user = decode_web_token(request.headers['Authorization'])
    except jwt.ExpiredSignatureError:
      print("Web token expired", 401)
      return util.return_error('expired_token')
    except (jwt.InvalidTokenError, KeyError):
      print("Missing or invalid token.")
      return util.return_error('invalid_token', 403)
    except Exception as e:
      print(f"Error decoding token: {e}")
      return util.return_error('invalid_token', 403)

    try:
      return func(user, *args, **kwargs)
    except Exception as e:
      print(f"Error in {str(func)}: {e}")
      return util.return_error('invalid_token', 403)
    
  wrapper.__name__ = func.__name__
  return wrapper

def check_if_admin(func):
  def wrapper(user):
    try:
      print(f"user: {user}")
      if user['role'] != 'admin':
        return util.return_error('not_authorized', 403)
      else:
        response = func(user)
        return response
    except Exception as e:
      print(f"Error in: {str(func)}: {e}")
      return util.return_error('unknown_error', 400)
  wrapper.__name__ = func.__name__
  return wrapper
