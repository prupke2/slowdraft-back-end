import datetime
import config
import jwt

def generate_web_token(my_team, access_token, refresh_token):
  expiry = datetime.datetime.now() + datetime.timedelta(seconds=3888000)
  # 3888000 # expires 45 days in the future
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
  print(f"payload: {payload}")
  return jwt.encode(payload, config.client_secret, algorithm="HS256")

def decode_web_token(token):
  try: 
    return jwt.decode(token, config.client_secret, issuer="SlowDraft", algorithms="HS256")
  except jwt.ExpiredSignatureError:
    print("web token expired")
    return None
