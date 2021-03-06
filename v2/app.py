import os

from flask import Flask, render_template, request, redirect, url_for

from flask_wtf import FlaskForm

from wtforms import StringField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired

from werkzeug.contrib.cache import SimpleCache

import db, songs

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

	cache = SimpleCache()

	class SearchForm(FlaskForm):
		artist_name = StringField(default = 'george ezra', validators = [DataRequired()])

	class RecommendForm(FlaskForm):
		form_name = HiddenField('form_name', id = 'form_name_recommend')
		main_artist = HiddenField('main_artist')
		artist_name = StringField(default = 'sigrid', validators = [DataRequired()])
		submit = SubmitField()

	class FeedbackForm(FlaskForm):
		form_name = HiddenField('form_name', id = 'form_name_feedback')
		user = StringField(default = 'anonymous')
		comment = TextAreaField(validators = [DataRequired()])
		submit = SubmitField()

	# class VoteForm(FlaskForm):
	# 	form_name = HiddenField('form_name', id = 'form_name_vote')
	# 	artist_id = HiddenField('artist_id')
	# 	vote_recording = HiddenField('vote_recording')


	@app.route('/')
	def base():
		feedback_form = FeedbackForm(form_name = 'feedback')
		search_form = SearchForm()

		charts = songs.getCharts()[0:10]
		cache.set('charts', charts)

		if request.args.get('artist_name') is not None:
			search_form = SearchForm(request.args)
			
			artist_name = search_form.artist_name.data
			artist = songs.buildArtist(artist_name) ##TODO add album

			recommend_form = RecommendForm(
				form_name = 'recommend', 
				main_artist = artist_name
				)

			# if request.args.get('track'):
			# 	##TODO return in correct sorted order based on prior to refreshing
			# 	artist = songs.upvote(artistName, request.args.get('track'))

			cache.set('main_artist', artist)
			recordings = artist.get('recordings')
			relationships = []
			for relationship in artist.get('relationships'):
				print("Relationship: ", relationship)
				##TODO Fix Somehow this is None
				print(artist.get('relationships').get(relationship))
				relationships.append([songs.getArtistName(relationship), relationship, artist.get('relationships').get(relationship)])
			print(relationships)

			similar_sounding = songs.getArtistId(artist_name, 4)
			print(similar_sounding)
			cache.set('similar_sounding', similar_sounding)

			return render_template(
				'artist.html', 
				artist_name = artist_name,
				artist_id = artist.get('artistId'),  
				feedback_form = feedback_form, 
				search_form = search_form, 
				recommend_form = recommend_form, 
				recordings = recordings, 
				relationships = relationships, 
				similar_sounding = similar_sounding
				)

		return render_template(
			'base.html', 
			feedback_form = feedback_form, 
			search_form = search_form, 
			charts = charts
			)

	@app.route('/', methods = ['POST', 'GET'])
	def post():
		database = db.getDb()
		print(database)
		print(request)
		print(request.form)

		if request.method == 'POST':

			if request.form.get('form_name') == 'feedback':
				feedback_form = FeedbackForm(request.form)

				user = feedback_form.user.data
				comment = feedback_form.comment.data

				database.execute('INSERT INTO post (user, comment) VALUES (?, ?)', (user, comment))
				database.commit()
				print('success')

				return redirect(url_for('base'))

			elif request.form.get('form_name') == 'recommend':
				recommend_form = RecommendForm(request.form)
				feedback_form = FeedbackForm(form_name = 'feedback')
				search_form = SearchForm()

				main_artist = cache.get('main_artist')

				main_name = recommend_form.main_artist.data
				second_name = recommend_form.artist_name.data

				print("ADDING RELATIONSHIP")
				##TODO Optimise
				main_artist['relationships'][songs.getArtistId(second_name)] = songs.addRelationship(second_name, main_artist.get('artistName'))
				print(main_artist.get('relationships'))

				relationships = []
				for relationship in main_artist.get('relationships'):
					print("Relationship: ", relationship)
					##TODO Fix Somehow this is None
					print(main_artist.get('relationships').get(relationship))
					relationships.append([songs.getArtistName(relationship), relationship, main_artist.get('relationships').get(relationship)])

				print(relationships)
				cache.set('main_artist', main_artist)

				print(feedback_form.form_name)
				feedback_form.form_name.data = 'feedback'
				print(feedback_form.form_name)

				return render_template(
					'artist.html', 
					artist_name = main_name, 
					artist_id = main_artist.get('artistId'),  
					feedback_form = feedback_form, 
					search_form = search_form, 
					recommend_form = recommend_form, 
					recordings = main_artist.get('recordings'), 
					relationships = relationships, 
					similar_sounding = cache.get('similar_sounding')
					)

			elif request.form.get('form_name') == 'vote':
				artist_id = request.form.get('artist_id')
				print(artist_id)
				vote_recording = request.form.get('vote_recording')
				print(vote_recording)
				vote_direction = request.form.get('vote_direction')
				print(vote_direction)

				if vote_direction == '\u21D1':
					artist = songs.upvote(artist_id, vote_recording)
					cache.set('main_artist', artist)
				else:
					artist = cache.get('main_artist')
					if artist == None:
						artist = songs.buildArtistWithId(artist_id)
						cache.set('main_artist', artist)
				
				relationships = []
				for relationship in artist.get('relationships'):
					print("Relationship: ", relationship)
					##TODO Fix Somehow this is None
					print(artist.get('relationships').get(relationship))
					relationships.append([songs.getArtistName(relationship), relationship, artist.get('relationships').get(relationship)])

				recommend_form = RecommendForm(
					form_name = 'recommend', 
					main_artist = artist.get('artistName')
					)
				recommend_form.form_name.data = 'recommend'

				feedback_form = FeedbackForm(form_name = 'feedback')
				print(feedback_form.form_name)
				feedback_form.form_name.data = 'feedback'
				print(feedback_form.form_name)

				return render_template(
					'artist.html', 
					artist_name = artist.get('artistName'), 
					artist_id = artist.get('artistId'),  
					feedback_form = feedback_form, 
					search_form = SearchForm(), 
					recommend_form = recommend_form,  
					recordings = artist.get('recordings'), 
					relationships = relationships, 
					similar_sounding = cache.get('similar_sounding')
					)

			elif request.form.get('form_name') == 'sort':
				sort_order = request.form.get('sort_order')
				print(sort_order)
				artist_id = request.form.get('artist_id')

				if sort_order == 'sort_votes':
					sort_method = songs.Sort.VOTES
				else:
					sort_method = songs.Sort.ALPHABETICAL

				artist = songs.sortRecordings(artist_id, songs.ArtistInput.ARTIST_ID, sort_method)
				cache.set('main_artist', artist)

				relationships = []
				for relationship in artist.get('relationships'):
					print("Relationship: ", relationship)
					##TODO Fix Somehow this is None
					print(artist.get('relationships').get(relationship))
					relationships.append([songs.getArtistName(relationship), relationship, artist.get('relationships').get(relationship)])
				print(relationships)

				similar_sounding = cache.get('similar_sounding')
				if similar_sounding == None:
					similar_sounding = songs.getArtistId(artist.get('artistName'), 4)
					print(similar_sounding)
					cache.set('similar_sounding', similar_sounding)

				recommend_form = RecommendForm(
					form_name = 'recommend', 
					main_artist = artist.get('artistName')
					)
				recommend_form.form_name.data = 'recommend'

				feedback_form = FeedbackForm(form_name = 'feedback')
				print(feedback_form.form_name)
				feedback_form.form_name.data = 'feedback'
				print(feedback_form.form_name)

				return render_template(
					'artist.html', 
					artist_name = artist.get('artistName'), 
					artist_id = artist_id,  
					feedback_form = feedback_form, 
					search_form = SearchForm(), 
					recommend_form = recommend_form, 
					recordings = artist.get('recordings'), 
					relationships = relationships, 
					similar_sounding = similar_sounding
				)

			else:
				print(request)
				print(request.query_string)

		return redirect(url_for('base'))

	@app.route('/id/<artist_id>')
	def get_artist(artist_id):
		feedback_form = FeedbackForm(form_name = 'feedback')
		search_form = SearchForm()

		artist = songs.buildArtistWithId(artist_id)
		artist_name = artist.get('artistName')

		recommend_form = RecommendForm(
			form_name = 'recommend', 
			main_artist = artist_name
			)

		# if request.args.get('track'):
		# 	##TODO return in correct sorted order based on prior to refreshing
		# 	artist = songs.upvote(artistName, request.args.get('track'))

		cache.set('main_artist', artist)
		recordings = artist.get('recordings')
		relationships = []
		for relationship in artist.get('relationships'):
			print("Relationship: ", relationship)
			##TODO Fix Somehow this is None
			print(artist.get('relationships').get(relationship))
			relationships.append([songs.getArtistName(relationship), relationship, artist.get('relationships').get(relationship)])
		print(relationships)

		similar_sounding = songs.getArtistId(artist_name, 4)
		print(similar_sounding)
		cache.set('similar_sounding', similar_sounding)

		return render_template(
			'artist.html', 
			artist_name = artist_name, 
			artist_id = artist.get('artistId'),  
			feedback_form = feedback_form, 
			search_form = search_form, 
			recommend_form = recommend_form, 
			recordings = recordings, 
			relationships = relationships, 
			similar_sounding = similar_sounding
		)

	return app