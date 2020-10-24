from flask import Flask, session, request, url_for, redirect, render_template, jsonify, flash, send_from_directory

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
	return "Hello world"

if __name__== '__main__':
  app.run(debug=True)
