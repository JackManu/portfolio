from ast import Try
from flask import Flask,render_template, url_for
import json
import sys
import os

import requests
import datetime
import sqlite3
import jinja2
sys.path.insert(0,os.path.abspath('services'))
from helper import Helper, HelperException

from pathlib import Path
# Create an instance of the Flask class that is the WSGI application.
# The first argument is the name of the application module or package,
# typically __name__ when using a single module.
TEMPLATE_DIR = os.path.abspath('templates')
STATIC_DIR = os.path.abspath('static')
app = Flask(__name__,template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# Flask route decorators 
#
#map / and /hello to the hello function.
# To add other resources, create functions that generate the page contents
# and add decorators to define the appropriate resource locators for them.

@app.route("/aboutme")
def aboutme():
    return render_template("aboutme.html")
@app.route("/aboutthis")
def aboutme():
    return render_template("aboutthis.html")
@app.route("/musicians_albums")
def musicians_albums():
    content={'musicians':['Tony Williams','John McLaughlin'],'albums':['Believe It','Birds of Fire']}
    return render_template("musicians_albums.html",content=content)
@app.route('/')
@app.route('/index')
def index():
   # Render the page
   return render_template('index.html',debug=True)

 


if __name__ == '__main__':
   # Run the app server on localhost:4449
   app.run('localhost', 4449)

