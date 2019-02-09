function updateAction() {
	var form = document.getElementById("searchForm");
	console.log(form);
	form.action = "{{ url_for(\'result\', artistName = \'george ezra\') }}";
	console.log(form.action);
	console.log(document.getElementById('artist').value);
}