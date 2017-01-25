import os
from urllib.parse import urlparse
from contextlib import closing
from flask import g


class DatabaseWrapper(object):
    """We cried, so you don't have to."""
    def __init__(self, db):
        self.db = db

    def close(self):
        self.db.close()

    def _fix(self, x):
        return x

    def select(self, query, args=[]):
        with closing(self.db.cursor()) as cur:
            cur.execute(self._fix(query), args)

            col_names = [c[0] for c in cur.description]
            return [dict(zip(col_names, cols)) for cols in cur.fetchall()]

    def execute(self, query, args=[]):
        with closing(self.db.cursor()) as cur:
            cur.execute(self._fix(query), args)
            self.db.commit()


class PostgresWrapper(DatabaseWrapper):
    def _fix(self, query):
        return query.replace('?', '%s')


if 'DATABASE_URL' in os.environ:
    import psycopg2
    import urllib.parse

    urllib.parse.uses_netloc.append("postgres")
    db_url = urlparse(os.environ["DATABASE_URL"])

    def get_db():
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = psycopg2.connect(
                database=db_url.path[1:],
                user=db_url.username,
                password=db_url.password,
                host=db_url.hostname,
                port=db_url.port
            )

        return PostgresWrapper(db)
else:
    import sqlite3

    def get_db():
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect('database.sqlite3')
        return DatabaseWrapper(db)


def setup_db(app):
    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()
