#!/usr/bin/env python3

import os

from flask import Flask, render_template, redirect, url_for, request, send_file
from db import setup_db, get_db

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = bool(os.environ.get('FLASK_DEBUG', 1))
setup_db(app)

@app.route('/add_meme', methods=['POST'])
def add_meme():
    bg_url = request.form['image']
    top_caption = request.form['top_caption']
    bottom_caption = request.form['bottom_caption']

    get_db().execute('INSERT INTO memes(url, caption1, caption2) VALUES(?, ?, ?);', (
        bg_url,
        top_caption,
        bottom_caption,
    ))

    return redirect(url_for('index'))

@app.route('/comment/<meme_id>', methods=['POST'])
def add_comment(meme_id):
    author = request.form['author']
    message = request.form['message']

    get_db().execute('INSERT INTO comments (author, messsage, meme_id) VALUES (?, ?, ?);', [
        author,
        message,
        meme_id
    ])

    return redirect(url_for('show', id=meme_id))


@app.route('/like_meme/<id>')
def like_meme(id):
    get_db().execute('UPDATE memes SET likes = likes + 1 WHERE id = ?', [id])
    return redirect(request.referrer)

@app.route('/meme/<id>')
def show(id):
    meme = get_db().select('SELECT * FROM memes WHERE id=?;', [int(id)])[0]
    meme['comments'] = get_db().select('SELECT * FROM comments WHERE meme_id = ?', [int(meme['id'])])
    meme['num_comments'] = len(meme['comments'])
    return render_template('show.html', meme=meme)

@app.route('/meme_form')
def meme_form():
    id = request.args.get('based_on', '')
    if id != '':
        meme = get_db().select('SELECT url FROM memes WHERE id=?;', [id])[0]
        url = meme['url']
    else:
        url = ''
    return render_template('meme-form.html', url=url)

def render_memes_page(order_by):
    memes = get_db().select('SELECT id, url, caption1, caption2, likes FROM memes ORDER BY ' + order_by + ' DESC;')
    for meme in memes:
        num_comments_results = get_db().select('SELECT COUNT(*) AS num FROM comments WHERE meme_id = ?', [int(meme['id'])])
        meme['num_comments'] = num_comments_results[0]['num']
    return render_template('homepage.html', memes=memes, order_by=order_by)

@app.route('/')
def index():
    # Popular ones (most likes first)
    # ORDER BY likes DESC
    return render_memes_page('likes')

@app.route('/fresh')
def fresh_memes():
    # Newest ones (newest first)
    # ORDER BY id DESC
    return render_memes_page('id')

def chunk(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

app.jinja_env.globals.update(chunk=chunk)

if __name__ == '__main__':
    app.run(host=os.environ.get('BIND_TO', '127.0.0.1'),
            port=int(os.environ.get('PORT', 5000)),
            debug=bool(int(os.environ.get('FLASK_DEBUG', 1))))
