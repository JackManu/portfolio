from ast import Try
from flask import Flask,render_template, request
import sys
import os

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
    insert_choices=request.form.get('insert_choices','nothing')
    return render_template("wiki_search.html")
@app.route("/wiki_search",methods=['POST','GET'])
def wiki_search():
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
    '''
    if len(content.keys()) > 0:
        return render_template("wiki_search_results.html")
    else:
    '''
    return render_template("wiki_search.html",content=content)
'''
@app.route('/albums')
def albums():
    content={}
    return render_template("albums.html",content=content)
'''
@app.route('/')
@app.route('/index')
def index():
   # Render the page
   return render_template('index.html',debug=True)

 


if __name__ == '__main__':
   # Run the app server on localhost:4449
   app.run('localhost', 4449)

