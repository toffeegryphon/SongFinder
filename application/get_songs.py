import os, urllib.request, json, csv
from unidecode import unidecode

BASE_URL = "https://musicbrainz.org/ws/2/"
QUERY_ARTIST = "lana+del+rey"

def getArtistName(artistId):
    print("Requesting name of %s" % (artistId))
    REQUEST_ARTIST_NAME = "%sartist/%s?fmt=json" % (BASE_URL, artistId)
    print(REQUEST_ARTIST_NAME)
    requestArtistName = urllib.request.urlopen(urllib.request.Request(REQUEST_ARTIST_NAME)).read().decode("utf-8")
    artistName = json.loads(requestArtistName).get('name')
    return artistName

def getArtistId(artist, numberOfResults = 1):
    ##TODO Check if artist name is same as the one obtained from ID
    print("Requesting %s's artist ID" % (artist))
    QUERY_ARTIST = artist.lower().replace(" ", "+")
    ##REQUEST_ARTIST_ID = BASE_URL + "artist/?query=" + QUERY_ARTIST + "&limit=1&fmt=json"
    REQUEST_ARTIST_ID = "%sartist/?query=%s&limit=%s&fmt=json" % (BASE_URL, QUERY_ARTIST, str(numberOfResults))
    print(REQUEST_ARTIST_ID)
    requestArtistId = urllib.request.urlopen(urllib.request.Request(REQUEST_ARTIST_ID)).read().decode("utf-8")

    if numberOfResults != 1:
        artistIds = {}
        artists = json.loads(requestArtistId).get('artists')
        for artist in artists:
            artistIds.update({artist.get('id') : artist.get('name')})
        return artistIds


    artistId = json.loads(requestArtistId).get('artists')[0].get('id')
    return artistId

def getSongsByArtistId(artistId, offset=None, songlist=None):
    ##TODO Fix heroku throws 500 Internal Server Error @ ~ page 12
    print("Requesting raw list of %s's recordings" % (artistId))
    if offset == None:
        offset = 0
    if songlist == None:
        songlist = []
    ##print("LENGTH SONGLIST: " + str(len(songlist)))
    ##artistId = artistId
    ##REQUEST_SONGS = BASE_URL + "recording?artist=" + artistId + "&limit=100&offset=" + str(offset) + "&fmt=json"
    REQUEST_SONGS = "%srecording?artist=%s&limit=100&offset=%s&fmt=json" % (BASE_URL, artistId, str(offset))
    print(REQUEST_SONGS)
    requestSongs = urllib.request.urlopen(urllib.request.Request(REQUEST_SONGS)).read().decode("utf-8")
    songs = json.loads(requestSongs)
    recordingCount = songs.get("recording-count")
    ##print(recordingCount)
    songlist.extend(songs.get("recordings"))
    while len(songlist) < recordingCount:
        offset += 100
        getSongsByArtistId(artistId, offset, songlist)
    ##print("FINISHED WHILE LOOP")
    ##print(json.dumps(songlist, indent=4))
    else:
        print(len(songlist))
        with open("%s_raw.json" % (artistId), 'w') as songsFile:
            json.dump(songlist, songsFile, indent=4)

        songlist = sorted(songlist, key = lambda song: song.get("title"))
    return songlist

##TODO determine if it is faster to remove unneccessary fields first then sort and shrink, or vice versa

def cleanList(songlist, artistId):
    
    print("Cleaning up list of %s's recordings" % (artistId))

    songlistClean = []
    first = songlist[0]
    first.pop("video")
    first.pop("length")
    first.pop("disambiguation")
    first.update({"title" : unidecode(first.get("title")), "albums" : None})
    songlistClean.append(first)
    print(songlistClean)

    ##TODO Optimise
    for song in songlist:
        #songTitle = song.get("title").lower().replace(" ", "").replace(",", "").replace("’", "").replace("'", "").replace("&", "and")
        songTitle = song.get("title").lower()
        if '(' in songTitle:
            start = songTitle.rfind('(')
            end = songTitle.rfind(')')
            ##print("start: " + str(start))
            ##print("end: " + str(end))
            songTitle = songTitle.replace(songTitle[start-1:end+1], "").replace(" ", "").replace(",", "").replace("’", "").replace("'", "").replace("&", "and")
            songTitle = unidecode(songTitle)
            ##print(songTitle)

        else:
            songTitle = song.get("title").lower().replace(" ", "").replace(",", "").replace("’", "").replace("'", "").replace("&", "and")
            songTitle = unidecode(songTitle)

        print(songTitle)
        
        for songC in songlistClean:
            songCTitle = songC.get("title").lower().replace(" ", "").replace(",", "").replace("’", "").replace("'", "").replace("&", "and")
            songCTitle = unidecode(songCTitle)
    
            if songCTitle in songTitle or songTitle in songCTitle:
                print("It exists")
                break

        else:
            print(song)
            song.pop("video")
            song.pop("length")
            song.pop("disambiguation")
            ##TODO Find a less hacky workaround

            #songTitle = song.get("title").replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")
            songTitle = song.get('title')
            if '(' in songTitle:
                start = songTitle.rfind('(')
                end = songTitle.rfind(')')
                ##print("start: " + str(start))
                ##print("end: " + str(end))
                songTitle = songTitle.replace(songTitle[start-1:end+1], "")
                ##print(songTitle)

            #song.update({"title" : songTitle.replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'"), "albums" : None})
            song.update({"title" : songTitle, "albums" : None})
            songlistClean.append(song)
            print(json.dumps(song, indent = 4))

    ##print(json.dumps(songlistClean, indent=4))

    ##print(len(songlist))
    ##print(len(songlistClean))

    with open("%s_clean.json" % (artistId), 'w') as songsFile:
        json.dump(songlistClean, songsFile, indent=4)

    return songlistClean

##getAlbumsOfSong("young+and+beautiful", "b7539c32-53e7-4908-bda3-81449c367da6")
def getAlbumsOfSong(songTitle, artistId):
    print("Getting albums each recording is published in")
    QUERY_SONG = songTitle.lower().replace(" ", "+").replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")
    REQUEST_ALBUMS = BASE_URL + "recording/?query=" + QUERY_SONG + "+AND+arid%3A\"" + artistId + "\"&release|status=official|type=album&limit=50&fmt=json"
    print(REQUEST_ALBUMS)
    requestAlbums = urllib.request.urlopen(urllib.request.Request(REQUEST_ALBUMS)).read().decode("utf-8")
    albums = json.loads(requestAlbums).get("recordings")
    
    albumsClean = []
    for entry in albums:
        entryClean = {}
        if QUERY_SONG.replace("+", "") in entry.get("title").lower().replace(" ", ""):

            for entryC in albumsClean:
                try:
                    if entry.get("releases")[0].get("id") == entryC.get("id") or entry.get("releases")[0].get("title") in entryC.get("releases") or entryC.get("releases") in entry.get("releases")[0].get("title"):
                        break
                except:
                    pass
            else:
                try:
                    entryClean.update({"id": entry.get("releases")[0].get("id"), "releases" : entry.get("releases")[0].get("title").replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")})
                    albumsClean.append(entryClean)
                except:
                    pass
                
    print(json.dumps(albumsClean, indent = 4))
    return albumsClean

def getSongsByArtist(artist, getAlbumsOfSongs = False):
    artistId = getArtistId(artist)

    songlist = cleanList(getSongsByArtistId(artistId), artistId)
    ##TODO Optimise
    if getAlbumsOfSongs:
        for song in songlist:
            albumlist = getAlbumsOfSong(song.get("title"), artistId)
            print(albumlist)
            song.update({"albums" : albumlist})
            print(json.dumps(song, indent = 4))
        with open("%s_clean.json" % (artistId), 'w') as songsFile:
            json.dump(songlist, songsFile, indent=4)
        ##console.log(json.dumps(songlist, indent=4))
    return songlist

##TODO Add versions. If version does not match, delete file and rebuild
def buildArtist(artistName, getAlbumsOfSongs = False):
    artistId = getArtistId(artistName)

    if os.path.isfile('./%s.json' % (artistId)):
        print("Artist already exists")
        with open('./%s.json' % (artistId), 'r') as artistFile:
            return json.load(artistFile)

    print("Building %s's artist profile" % (artistName))
    artist = {"artistId" : artistId, "artistName" : artistName}

    if os.path.isfile('./%s_clean.json' % (artistId)):
        print('./%s_clean.json' % (artistId))
        with open('./%s_clean.json' % (artistId), 'r') as songsFile:
            songs = json.load(songsFile)

    else:
        songs = getSongsByArtist(artistName, getAlbumsOfSongs)

    ##Build Artist
    artist.update({"recording-count" : len(songs), "recordings" : songs, "relationships" : {}})
    print(json.dumps(artist, indent = 4))

    with open('%s.json' % (artistId), 'w') as artistFile:
        json.dump(artist, artistFile, indent = 4)

    return artist

def buildArtistWithId(artistId, getAlbumsOfSongs = False):
    if os.path.isfile('./%s.json' % (artistId)):
        print("Artist already exists")
        with open('./%s.json' % (artistId), 'r') as artistFile:
            return json.load(artistFile)

    print("Building %s's artist profile" % (artistName))
    artist = {"artistId" : artistId, "artistName" : artistName}

    if os.path.isfile('./%s_clean.json' % (artistId)):
        print('./%s_clean.json' % (artistId))
        with open('./%s_clean.json' % (artistId), 'r') as songsFile:
            songs = json.load(songsFile)

    else:
        songs = getSongsByArtist(artistName, getAlbumsOfSongs)

    ##Build Artist
    artist.update({"recording-count" : len(songs), "recordings" : songs, "relationships" : {}})
    print(json.dumps(artist, indent = 4))

    with open('%s.json' % (artistId), 'w') as artistFile:
        json.dump(artist, artistFile, indent = 4)

    return artist

def addRelationship(secondArtistName, mainArtistName):

    mainId = getArtistId(mainArtistName)
    secondId = getArtistId(secondArtistName)

    ##Does it automatically see which lines have changed and update those only? Or do I have to do it manually?
    if os.path.isfile('./%s.json' % (mainId)):
        with open('./%s.json' % (mainId), 'r') as mainArtistFile:
            mainArtist = json.load(mainArtistFile)
    else:
        mainArtist = buildArtist(mainArtistName)

    if os.path.isfile('./%s.json' % (secondId)):
        with open('./%s.json' % (secondId), 'r') as secondArtistFile:
            secondArtist = json.load(secondArtistFile)
    else:
        secondArtist = buildArtist(secondArtistName)

    print(json.dumps(mainArtist, indent = 4))
    print(json.dumps(secondArtist, indent = 4))

    ##TODO Optimise
    if secondId in mainArtist.get("relationships"):
        print("Relationship exists, incrementing...")
        mainArtist["relationships"][secondId] += 1

    else:
        print("Relationship does not exist, adding...")
        mainArtist["relationships"][secondId] = 1

    if mainId in secondArtist.get("relationships"):
        print("Relationship exists, incrementing...")
        secondArtist["relationships"][mainId] += 1

    else:
        print("Relationship does not exist, adding...")
        secondArtist["relationships"][mainId] = 1

    print("New relationship value is %s" % str(mainArtist.get("relationships").get(secondId)))

    with open('./%s.json' % (mainId), 'w') as mainArtistFile:
        json.dump(mainArtist, mainArtistFile, indent = 4)

    with open('./%s.json' % (secondId), 'w') as secondArtistFile:
        json.dump(secondArtist, secondArtistFile, indent = 4)

    return(mainArtist.get("relationships").get(secondId))

SPOTIFY_BASE = 'https://spotifycharts.com/'
SPOTIFY_DEFAULT = '%s/regional/global/daily/latest/download' % SPOTIFY_BASE

def getCharts():
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)

    requestCharts = urllib.request.urlretrieve(SPOTIFY_DEFAULT, 'charts.csv')

    #TODO Most likely can be removed
    with open('charts.csv', 'r') as file, open('charts_clean.csv', 'w') as output:
        next(file)
        for line in file:
            output.write(line)

    charts = []
    with open('charts_clean.csv', 'r') as file:
        chartsCSV = csv.DictReader(file)
        line = 1
        for row in chartsCSV:
            charts.append({'position' : row['Position'], 'trackName' : row['Track Name'], 'artist' : row['Artist'], 'streams' : row['Streams'], 'url' : row['URL']})
    #print(charts)

    ##Reset header, if not musicbrainz calls do not work
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0')]
    urllib.request.install_opener(opener)

    return charts