from ast import Try
from flask import Flask,render_template, request,jsonify
import sys
import os
import re
import json
from urllib.parse import unquote

#sys.path.insert(0,os.path.abspath('services'))
# Create an instance of the Flask class that is the WSGI application.
# The first argument is the name of the application module or package,
# typically __name__ when using a single module.
TEMPLATE_DIR = os.path.abspath('templates')
STATIC_DIR = os.path.abspath('static')
from services import Wikipedia_reader,Youtube_reader
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
def aboutthis():
    return render_template("aboutthis.html")
@app.route("/wiki_insert",methods=['POST'])
def wiki_insert():
    content={}
    insert_dicts=[]
    for each in request.form:
        print(f"Get from form: {request.form.get(each)}")
        insert_dicts.append(request.form.get(each))  
    '''
    insert into db
    '''

    return render_template("wiki_search.html",content=content)
@app.route("/wiki_search_results",methods=['POST'])
def wiki_search_results():
    rule = request.url_rule
    content={}
    if request.method == 'POST':
        searchs=request.form.get('search_button','nothing')
        num_pages=request.form.get('pages',5)
        wiki=Wikipedia_reader(searchs,num_pages)
        try:
            content=wiki.get_pages()
        except Exception as e:
            content['errors'].append(f"Exception in wiki.get_pages in main.py")
    return render_template("wiki_search_results.html",content=content)

@app.route("/wiki_search")
def wiki_search():
    content={}
    return render_template("wiki_search.html",content=content)

@app.route('/')
@app.route('/index')
def index():
   # Render the page
   return render_template('index.html',debug=True)

 


if __name__ == '__main__':
   # Run the app server on localhost:4449
   app.run('localhost', 4449)

