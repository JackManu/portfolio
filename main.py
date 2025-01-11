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
import wiki_youtube_reader
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
@app.route("/musicians",methods=['POST','GET'])
def musicians():
    content=[]
    if request.method == 'POST':
        #content={'musicians':[f'search button contents {request.form.get("search_button","not found")}'],'albums':[]}
        wiki=wiki_youtube_reader.Wikipedia_reader(request.form.get('search_button','nothing'))
        try:
            content=wiki.get_pages()
        except Exception as e:
            content.append({'artist':'Error','title':f'{e}','excerpt':'failure in wiki.get_pages()','url':'please tell doug'})
    return render_template("musicians.html",content=content)
@app.route("/albums",methods=['POST','GET'])
def albums():
    content={'artists':['Miles Davis'],'albums':['Bitches Brew','Live Evil']}
    return render_template("albums.html",content=content)
@app.route('/')
@app.route('/index')
def index():
   # Render the page
   return render_template('index.html',debug=True)

 


if __name__ == '__main__':
   # Run the app server on localhost:4449
   app.run('localhost', 4449)

