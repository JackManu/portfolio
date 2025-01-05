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


@app.route('/')
def index():
   # Render the page
   '''
   try:
       helper=Helper()
       output_html=helper.render_html()
   except HelperException as e:
       return f'<HTML><BODY>HelperException Encountered a problem rendering HTML\n{e}' \
              + f' Context: {e.__context__}'\
              + f' Cause:   {e.__cause__}' \
              + f' Traceback: {e.__traceback__}'
   except Exception as e:
       return f'<HTML><BODY>Encountered a problem generating the page\n{e}'
   else:
       return output_html
   '''
   return render_template('index.html',debug=True)

 


if __name__ == '__main__':
   # Run the app server on localhost:4449
   app.run('localhost', 4449)

