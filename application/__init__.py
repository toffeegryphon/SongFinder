from flask import Flask, render_template, request
import application.get_songs as util

app = Flask(__name__)

@app.route('/')
def main():
	return render_template('main.html')

@app.route('/', methods = ['POST', 'GET'])
def result():
	if request.method == 'POST':
		artist = request.form.get('artist')
		print("artist: " + artist)
		print("getAlbum: " + str(request.form.get('getAlbum')))
		if artist != "":
			result = util.getSongsByArtist(artist, request.form.get('getAlbum'))
			print("ARTIST NOT EMPTY")
			return render_template("main_with_result.html", result = result)
	print("ARTIST EMPTY")
	##TODO Fix bug. Somehow, main_with_result throws error if result is used instead of res
	return render_template("main.html", res = "Please enter artist")

if __name__ == "__main__":
	app.run(debug=True)