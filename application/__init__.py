from flask import Flask, render_template, request
from werkzeug.contrib.cache import SimpleCache
import application.get_songs as songs

app = Flask(__name__)

cache = SimpleCache()

@app.route('/')
def main():

	charts = songs.getCharts()[0:10]
	cache.set('charts', charts)

	return render_template('main.html', charts = charts)

@app.route('/search/<artistName>', methods = ['POST', 'GET'])
def result(artistName):

	artistName = artistName
	print("RESULT CALLED")
	print(request.form.get('submit'))
	if request.method == 'POST' or request.method == 'GET':
		if request.form.get('submit') == 'search' or request.method == 'GET':
			print("artist: " + artistName)
			print("getAlbum: " + str(request.form.get('getAlbum')))

			if artistName != "":
				# mainArtist['name'] = artistName
				# mainArtist['id'] = songs.getArtistId(artistName)
				# print(mainArtist)

				artist = songs.buildArtist(artistName, request.form.get('getAlbum'))

				if request.args.get('track'):
					##TODO return in correct sorted order based on prior to refreshing
					artist = songs.upvote(artistName, request.args.get('track'))

				cache.set('mainArtist', artist)
				result = artist.get('recordings')
				relationships = []
				for relationship in artist.get('relationships'):
					print("Relationship: ", relationship)
					##TODO Fix Somehow this is None
					print(artist.get('relationships').get(relationship))
					relationships.append([songs.getArtistName(relationship), relationship, artist.get('relationships').get(relationship)])
				print(relationships)

				##result = songs.getSongsByArtist(artistName, request.form.get('getAlbum'))
				return render_template("main_with_result.html", result = result, relationships = relationships, artistName = artistName)

		elif request.form.get('submit') == 'Sort.VOTES' or request.form.get('submit') == 'Sort.ALPHABETICAL':
			if request.form.get('submit') == 'Sort.VOTES':
				sortMethod = songs.Sort.VOTES
			else:
				sortMethod = songs.Sort.ALPHABETICAL

			artist = songs.sortRecordings(artistName, songs.ArtistInput.ARTIST_NAME, sortMethod)

			cache.set('mainArtist', artist)
			result = artist.get('recordings')
			relationships = []
			for relationship in artist.get('relationships'):
				print("Relationship: ", relationship)
				##TODO Fix Somehow this is None
				print(artist.get('relationships').get(relationship))
				relationships.append([songs.getArtistName(relationship), relationship, artist.get('relationships').get(relationship)])
			print(relationships)

			return render_template('main_with_result.html', result = result, relationships = relationships, artistName = artistName)

		elif request.form.get('submit') == 'relationship':
			secondName = request.form.get('second')
			print("second: " + secondName)

			if not cache:
				return(render_template('main.html'))

			mainArtist = cache.get('mainArtist')
			print("mainArtist: ", mainArtist)
			print(mainArtist.get('artistName'))

			if secondName != "":
				print("ADDING RELATIONSHIP")
				##TODO Optimise
				mainArtist['relationships'][songs.getArtistId(secondName)] = songs.addRelationship(secondName, mainArtist.get('artistName'))
				print(mainArtist.get('relationships'))

				relationships = []
				for relationship in mainArtist.get('relationships'):
					print("Relationship: ", relationship)
					##TODO Fix Somehow this is None
					print(mainArtist.get('relationships').get(relationship))
					relationships.append([songs.getArtistName(relationship), relationship, mainArtist.get('relationships').get(relationship)])

				print(relationships)
				cache.set('mainArtist', mainArtist)
				return(render_template('main_with_result.html', result = mainArtist.get('recordings'), relationships = relationships, artistName = artistName))

	##TODO Fix bug. Somehow, main_with_result throws error if result is used instead of res
	return render_template("main.html", res = "Please enter artist")

# ##TODO make this work
# @app.route('/')
# def resultFromCharts():
# 	pass

if __name__ == "__main__":
	app.run(debug=True)