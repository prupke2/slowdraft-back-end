from app import *
import config
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def next_pick_email(to_email):
	try:
		print(f"Sending next pick email to: {to_email}...")
		message = Mail(
		from_email='slowdraftapp@gmail.com',
		to_emails=to_email,
		subject="You're up in the draft!",
		html_content="<div style='background: rgba(51, 153, 255, 0.3); font-size: 16px; " \
							"font-family: Verdana, Arial, sans-serif; padding: 10px;'>" \
							"<br><p style='font-size: 12px;'>It's your turn to pick in the draft!</p>" \
							"<p>" + config.site + "</p	>" \
							"<p style='font-size: 8px; text-align: right;'>© SlowDraft</p></div>")
		sg = SendGridAPIClient(config.SENDGRID_KEY)
		response = sg.send(message)
		print(f"status code: {response.status_code} response: {response.body}")
		return True
	except Exception as e:
		print(f"Failure sending email to {to_email}: {e}")
		return False
