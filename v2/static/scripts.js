function find_artist(artist_name) {
	console.log('Find ' + artist_name)

	var url = new URL(window.location.hostname);

	var params = {
		method: 'GET',
		cache: 'default',
	};

	var args = {
		artist_name: artist_name
	};

	Object.keys(args).forEach(key => url.searchParams.append(key, args[key]));

	var request = new Request(url, params);

	return fetch(request);
}