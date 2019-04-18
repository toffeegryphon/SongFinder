import os

from flask import Flask, render_template, request, redirect, url_for

from flask_wtf import FlaskForm

from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

import db

def create_app():
	app = Flask(__name__)

	app.config.from_mapping(
		SECRET_KEY = os.urandom(32),
		DATABASE = os.path.join(app.instance_path, 'flaskr.sqlite')
		)

	try:
		os.makedirs(app.instance_path)
	except OSError:
		pass

	db.initApp(app)

	class SearchForm(FlaskForm):
		artist_name = StringField(default = 'george ezra', validators = [DataRequired()])

	class FeedbackForm(FlaskForm):
		user = StringField(default = 'anonymous')
		comment = TextAreaField(validators = [DataRequired()])
		submit = SubmitField()


	@app.route('/')
	def base():
		feedback_form = FeedbackForm()
		search_form = SearchForm()

		if request.args.get('artist_name') is not None:
			search_form = SearchForm(request.args)
			artist_name = search_form.artist_name.data
			return render_template(
				'artist.html', 
				artist_name = artist_name, 
				feedback_form = feedback_form, 
				search_form = search_form,)

		return render_template(
			'base.html', 
			feedback_form = feedback_form, 
			search_form = search_form
			)

	@app.route('/', methods = ['POST', 'GET'])
	def post():
		database = db.getDb()
		print(database)
		print(request)
		print(request.form)

		if request.method == 'POST':
			feedback_form = FeedbackForm(request.form)

			user = feedback_form.user.data
			comment = feedback_form.comment.data

			database.execute('INSERT INTO post (user, comment) VALUES (?, ?)', (user, comment))
			database.commit()
			print('success')

			return redirect(url_for('base'))

		else:
			print(request)
			print(request.query_string)

		return redirect(url_for('base'))

	return app