import sqlite3

import click

from flask import current_app, g
from flask.cli import with_appcontext

def initApp(app):
	app.teardown_appcontext(closeDb)
	app.cli.add_command(initDbCommand)

def initDb():
	db = getDb()

	with current_app.open_resource('schema.sql') as file:
		db.executescript(file.read().decode('utf8'))

@click.command('init-db') ##Command line command called init-db that calls the initDb function and displays success message
@with_appcontext
def initDbCommand():
	initDb()
	click.echo('Initialised the database.')


def getDb():
	if 'db' not in g:
		g.db = sqlite3.connect(current_app.config['DATABASE'], detect_types = sqlite3.PARSE_DECLTYPES)
		g.db.row_factory = sqlite3.Row

	return g.db

def closeDb(e = None):
	db = g.pop('db', None)

	if db is not None:
		db.close()