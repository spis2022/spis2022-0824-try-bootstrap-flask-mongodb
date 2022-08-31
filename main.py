# TO USE:
#  (0) Set up a MongoDB database 
#  (1) Define secret MONGO_URI
#  (2) Define secrets
#      APP_SECRET_KEY,
#      GITHUB_CLIENT_ID
#      GITHUB_CLIENT_SECRET
#      Initially with arbitrary values
#  (3) Run web app to get the URL
#  (4) Follow instructions at link below
#      to get values for GITHUB_CLIENT_ID
#      and GITHUB_CLIENT_SECRET 
#  (5) Enjoy   
#  https://github.com/spis2022/spis2022.github.io/blob/main/webapps/oauth_setup.md
#



# For Bootstrap Flask (https://bootstrap-flask.readthedocs.io/en/stable/basic/)
# In Shell: python -m poetry add bootstrap-flask


from flask_bootstrap import Bootstrap5

import os
from datetime import datetime

from flask import Flask, url_for, render_template, request
from flask import redirect

from flask import g

from flask_github import GitHub 

# In Shell: python -m poetry add Flask-Session
from flask import session
from flask_session import Session

# For flash messages
# Categories: https://getbootstrap.com/docs/5.2/components/alerts/
# primary, secondary, success, danger, warning, info, light, dark
from flask import flash

app = Flask(__name__)

bootstrap = Bootstrap5(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


app.config['GITHUB_CLIENT_ID'] = os.environ['GITHUB_CLIENT_ID']
app.config['GITHUB_CLIENT_SECRET'] = os.environ['GITHUB_CLIENT_SECRET']

github = GitHub(app)

# In order to use "sessions",you need a "secret key".
# This is something random you generate.  
# Just type some arbitrary letters and numbers.
# See: http://flask.pocoo.org/docs/0.10/quickstart/#sessions
# Put it in an Secret

app.secret_key=os.environ['APP_SECRET_KEY']


# Set up access to MongoDB
# In Shell: 
#  python3 -m poetry add PyMongo
#  python3 -m poetry add dnspython

from pymongo import MongoClient
client = MongoClient(os.environ['MONGO_URI'])
db = client.database

# format
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class InterestForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])


@app.route('/')
def renderMain():
    print("session=",session)
    return render_template('home.html')

@app.route('/login')
def login():
    return github.authorize()

@app.route('/logout')
def logout():
    session.clear()
    return render_template('home.html')

@app.route('/interests')
def render_interests():
    interests = list(db.interests.find({}))
    return render_template('interests.html',
                           interests=interests,
                           form=InterestForm())

@app.route('/link2')
def render_link2():
    return render_template('link2.html')




@github.access_token_getter
def token_getter():
    if 'oauth_token' in g:
      return g.oauth_token
    else:
      return None

def store_user(user):
    '''
    Store currently logged in user in users if it isn't already there.
    '''
    # Look up user in users collection
    user_found = db.users.find_one({"login": user["login"]})
    if not user_found:
        db.users.insert_one(user)   
 
    
def update_last_login(user):
    '''
    Update the last_login field for the currently logged in user
    '''
    # Based in part on code from Nata/Mohammed's project
    # https://replit.com/@AnastasiyaVerth/webscraper-demo#templates/listings.html
   
    login = user['login']
    filter = {'login': login}
    new_values = { "$set": { 'last_login': datetime.now() } }
    db.users.update_one(filter, new_values)
    
@app.route('/callback')
@github.authorized_handler
def authorized(oauth_token):
    print("oauth_token=",oauth_token)
    if oauth_token is None:
        session.clear()
        return "Authorization failed."
    g.oauth_token = oauth_token
    try:
      session["user"] = github.get('/user')
      store_user(session["user"])
      update_last_login(session["user"])  
    except Exception as e:
      print("Exception",e)
      flash('Exception: ' + str(e), 'danger')

      session["user"] = None
    return redirect(url_for('renderMain'))
  
    
if __name__=="__main__":
    app.run(debug=True,host="0.0.0.0")