from app import *
from flask_mail import Mail, Message
import config

class InviteEmail(object):
	def __init__(self, invitation_code, recipients):

		email_body = str(session['name'] + " has invited you to join their SlowDraft league! \n\n" +
						 "Click the link below to join now! \n\n" +
						site + "/register/" + str(invitation_code))

		html_email_body = "<div style='background: rgba(244,251,244,1); font-size: 16px; " \
						  "font-family: Verdana, Arial, sans-serif; padding: 10px;'>" \
						  "" + str(session['name'] + " has invited you to join their SlowDraft league! <br><br>" \
						  "<a style='display: block; background-color: rgba(0, 128, 0, 1); " \
						  "color: white; padding: 6px 2px; margin: 25px auto; height: 25px; width: 180px; " \
						  "font-family: Verdana, Arial, sans-serif; font-size: 18px; text-align: center; " \
						  "border-width: 2px 0 0 2px; border-radius: 4px; outline: none; max-width: 100%; " \
						  "text-decoration: none;' " \
						  "href='http://" + site + "/register/" + invitation_code + "'>Join now</a><a></a>"
						  "<p style='font-size: 10px;'>© SlowDraft, Inc. All Rights Reserved. </p></div>")

		subject = "You have been invited to join SlowDraft"
		msg = Message("You have been invited to join SlowDraft",
					  sender="SlowDraft",
					  recipients=[recipients])
		msg.body = email_body
		msg.html = html_email_body
		try:
			mail.send(msg)
			print("Email sent!")
			# send_email(recipients, subject, html_email_body)
			# flash("Invitation Sent")
		except:
			msg = "Unable to send invitation email to " + recipients
			print(msg)

			# flash(msg, 'danger')

# msg = Message(subject,
#               sender="SlowDraft",
#               recipients=recipients)
# msg.body = email_body
# msg.html = html_email_body

		

def NextPickEmail(name, recipients):
	email_body = "It's your turn to pick in the draft, " + name + "! \n\n" \
	"Head to SlowDraft now to make your next pick:\n" \
	"http://" + config.site + "/players\n" \
	"http://" + config.site + "/shortlist"

	html_email_body = "<div style='background: rgba(51, 153, 255, 0.3); font-size: 16px; " \
					  "font-family: Verdana, Arial, sans-serif; padding: 10px;'>" \
					  "<a href='" + config.site + "/players'>" \
					  "<img src='https://slowdraft.herokuapp.com/static/slowdraft_logo.png'></a>" \
					  "<br>Hey " + name + ",<p style='font-size: 12px;'>It's your turn to pick in the draft!</p>" \
					  "<a style='display: block; border: 2px solid rgba(51, 102, 204, 1); " \
					  "color: white; padding: 6px 2px; margin: 25px auto; height: 25px; width: 180px; " \
					  "font-family: Verdana, Arial, sans-serif; font-size: 18px; text-align: center; " \
					  "border-width: 2px 0 0 2px; border-radius: 4px; outline: none; max-width: 100%; " \
					  "text-decoration: none; background-color: rgba(51, 102, 204, 1);' " \
					  "href='" + config.site + "/players'>Draft now!</a>" \
					  "<p style='font-size: 8px; text-align: right;'>© SlowDraft</p></div>"

	subject = "You're up in the draft, " + name
	msg = Message(subject, sender="SlowDraft", recipients=[recipients])
	msg.body = email_body
	msg.html = html_email_body
	return msg
