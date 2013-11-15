"""
    URL Short
    ~~~~~~

    A micro example application written as test

"""

import os, os.path, re, sqlite3, random, string

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

from contextlib import closing

# App Create
app = Flask(__name__)

# Database configs
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app.config.from_object(__name__)

# Connects to the DB
def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

# Creates the tables
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Opens a new database connection if there is none yet        
def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db        

# Sorthand for query to the database.
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv  

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# Helper to generate random URL string          
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size)) 

# Index
@app.route('/')
def hello():
    return render_template('index.html')

# Routing    
@app.route('/<short>')
def short(short=None):
    check_up = query_db('select * from entries where short = ?',[short],one=True)
    if check_up is None:
        error = "That shorten url doesn't yet exist. Shorten it now!"
        return render_template('index.html', error=error) 
    else:
        return redirect(check_up[1])
    

@app.route('/show_entries')
def show_entries():
    if not session.get('logged_in'):
        abort(401)
    cur = g.db.execute('select orig_url, short from entries order by id desc')
    entries = [dict(orig_url=row[0], short=row[1]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():

    test = True
    old_url = request.form['url']
    while(test):
        new_url = id_generator()
        lookup = query_db('select * from entries where short = ?', [new_url],one=True)

        if lookup is None:
            test=False
            g.db.execute('insert into entries (orig_url, short) values (?, ?)',
                       [old_url, new_url])
    
    g.db.commit()
    message = "Using /%s will now redirect you to %s" % (new_url,old_url)
    
    return render_template('index.html',message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            # flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('hello'))

    
if __name__ == '__main__':
    init_db()
    app.run()
    
        

