import urllib.request, json

BASE_URL = "https://musicbrainz.org/ws/2/"
QUERY_ARTIST = "lana+del+rey"

def getArtistId(artist):
    QUERY_ARTIST = artist.lower().replace(" ", "+")
    REQUEST_ARTIST_ID = BASE_URL + "artist/?query=" + QUERY_ARTIST + "&limit=1&fmt=json"
    print(REQUEST_ARTIST_ID)
    requestArtistId = urllib.request.urlopen(urllib.request.Request(REQUEST_ARTIST_ID)).read().decode("utf-8")
    artistId = json.loads(requestArtistId).get('artists')[0].get('id')
    return artistId

def getSongsByArtistId(artistId, offset=None, songlist=None):
    if offset == None:
        offset = 0
    if songlist == None:
        songlist = []
    ##print("LENGTH SONGLIST: " + str(len(songlist)))
    ##artistId = artistId
    REQUEST_SONGS = BASE_URL + "recording?artist=" + artistId + "&limit=100&offset=" + str(offset) + "&fmt=json"
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
    ##BUG? Calls subsequent lines multiple times
    ##print(json.dumps(songlist, indent=4))
    print(len(songlist))
    with open(artistId + ".json", "w") as songsFile:
        json.dump(songlist, songsFile, indent=4)

    songlist = sorted(songlist, key = lambda song: song.get("title"))
    return songlist

##TODO determine if it is faster to remove unneccessary fields first then sort and shrink, or vice versa

def cleanList(songlist, artistId):
    
    songlistClean = []
    first = songlist[0]
    first.pop("video")
    first.pop("length")
    first.pop("disambiguation")
    first.update({"albums" : None})
    songlistClean.append(first)
    ##print(songlistClean)

    ##TODO Optimise
    for song in songlist:
        songTitle = song.get("title").lower().replace(" ", "").replace(",", "").replace("’", "").replace("'", "").replace("&", "and")

        for songC in songlistClean:
            songCTitle = songC.get("title").lower().replace(" ", "").replace(",", "").replace("’", "").replace("'", "").replace("&", "and")

            if songCTitle in songTitle or songTitle in songCTitle:
                break

        else:
            song.pop("video")
            song.pop("length")
            song.pop("disambiguation")
            ##TODO Find a less hacky workaround
            song.update({"title" : song.get("title").replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'"), "albums" : None})
            songlistClean.append(song)
            print(json.dumps(song, indent = 4))

    ##print(json.dumps(songlistClean, indent=4))

    ##print(len(songlist))
    ##print(len(songlistClean))

    with open(artistId + "_clean.json", "w") as songsFile:
        json.dump(songlistClean, songsFile, indent=4)

    return songlistClean

##getAlbumsOfSong("young+and+beautiful", "b7539c32-53e7-4908-bda3-81449c367da6")
def getAlbumsOfSong(songTitle, artistId):
    QUERY_SONG = songTitle.lower().replace(" ", "+")
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
        with open(artistId + "_clean.json", "w") as songsFile:
            json.dump(songlist, songsFile, indent=4)
        ##console.log(json.dumps(songlist, indent=4))
    return songlist
