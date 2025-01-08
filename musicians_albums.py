from ast import Try
from flask import Flask,render_template, url_for
import json
import sys
import os
import requests
import datetime
import sqlite3
import jinja2
from pathlib import Path
sys.path.insert(0,os.path.abspath('services'))
TEMPLATE_DIR = os.path.abspath('templates')
STATIC_DIR = os.path.abspath('static')
app = Flask(__name__,template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
@app.route('/musicians_albums')
def musicians_albums():
    output_dict={'Tony Williams':'drums','John McLaughlin':'guitar'}
    return render_template('musicians_albums.html',**output_dict,debug=True)
   # Render the page

if __name__ == '__main__':
    app.run('localhost', 4449)