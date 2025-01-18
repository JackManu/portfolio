from ast import Try
import ast
from flask import Flask,render_template, request,jsonify
import sys
import os
import re
import json
import datetime
from urllib.parse import unquote

#sys.path.insert(0,os.path.abspath('services'))
# Create an instance of the Flask class that is the WSGI application.
# The first argument is the name of the application module or package,
# typically __name__ when using a single module.
TEMPLATE_DIR = os.path.abspath('templates')
STATIC_DIR = os.path.abspath('static')
from services import Wikipedia_reader,Youtube_reader,DB_helper
app = Flask(__name__,template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# Flask route decorators 
#
#map / and /hello to the hello function.
# To add other resources, create functions that generate the page contents
# and add decorators to define the appropriate resource locators for them.
def get_db():
    '''
    Function get_db()

    Get entries from the portfolio db 
    Wikipedia and Youtube tables.
    format into json for use in html/jinja
    '''
    mydb=DB_helper()
    wiki_output=mydb.exec_statement("select id,creation_date,search_text,title,url,description,thumbnail from Wikipedia order by search_text asc;")
    db_content={}
    db_content['pages']=[]
    for each in wiki_output:
        temp_dict={}
        temp_dict['id']=each[0]
        temp_dict['search_text']=each[2]
        temp_dict['title']=each[3]
        temp_dict['url']=each[4]
        temp_dict['description']=each[5]
        temp_dict['thumbnail']=ast.literal_eval(each[6])
        temp_dict['youtube_videos']=[]
        yt_select=mydb.exec_statement("select id,creation_date,wiki_id,video_id,title,url,description,thumbnail from Youtube where wiki_id = ? order by title asc;",temp_dict['id'])
        for each_yt in yt_select:
            yt={}
            yt['id']=each_yt[0]
            yt['wiki_id']=each_yt[2]
            yt['title']=each_yt[4]
            yt['url']=each_yt[5]
            yt['description']=each_yt[6]
            yt['thumbnail']=ast.literal_eval(each_yt[7])
            temp_dict['youtube_videos'].append(yt)
        print(f"In main.py get_db function temp_dict is :\n {json.dumps(temp_dict,indent=2)}")
        db_content['pages'].append(temp_dict)
    return db_content

@app.route("/aboutme")
def aboutme():
    return render_template("aboutme.html")
@app.route("/aboutthis")
def aboutthis():
    content={}
    return render_template("aboutthis.html",content=content)
@app.route("/delete_db",methods=['POST'])
def delete_db():
    '''
    Function delete_db

    It 'should' be as easy as just deleting the DB/portfolio.db file.
    It's been acting weird and I don't trust this, but maybe it was 
    because of other things
    '''
    db_content={}
    db_content['errors']=[]
    try:
        os.remove(os.path.abspath('DB/portfolio.db'))
    except Exception as e:
        db_content['errors'].append(f'Exception deleting ../DB/portfolio.db : {e}')
    return render_template("wiki_search.html",db_content={})
@app.route("/wiki_insert",methods=['POST'])
def wiki_insert():
    mydb=DB_helper()
    for each in mydb.alerts:
        print(f"DB Creation:  {each}")
    for k,v in request.form.items():
        my_dict=ast.literal_eval(v)
        youtube=Youtube_reader(f"{my_dict['title']} {my_dict['search_text']}",my_dict['id'])
        yt_out=youtube.load_db()
        for yt_each in yt_out:
            print(f"YOUTUBE OUT: {json.dumps(yt_each,indent=2)}")
        mydb.db_insert('Wikipedia',my_dict['id'],my_dict['search_text'],my_dict['title'],my_dict['url'],my_dict['description'],my_dict['thumbnail'])
    for each in mydb.alerts:
        print(f"Alert from DB_Helper: {each}")
    db_content=get_db()
    return render_template("wiki_search.html",db_content=db_content)
@app.route("/wiki_search")
def wiki_search():
    db_content=get_db()
    return render_template("wiki_search.html",db_content=db_content)

@app.route("/wiki_search_results",methods=['POST'])
def wiki_search_results():
    rule = request.url_rule
    content={}
    content['errors']=[]
    if request.method == 'POST':
        searchs=request.form.get('search_button','nothing')
        num_pages=request.form.get('pages',5)
        wiki=Wikipedia_reader(searchs,num_pages)
        try:
            content=wiki.get_pages()
        except Exception as e:
            content['errors'].append(f"Exception in wiki.get_pages in main.py")
    return render_template("wiki_search_results.html",search_content=content)

@app.route('/')
@app.route('/index')
def index():
   # Render the page
   return render_template('index.html',debug=True)

if __name__ == '__main__':
   # Run the app server on localhost:4449
   app.run('localhost', 4449)

