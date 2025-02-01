from ast import Try
import ast
from flask import Flask,render_template, request,redirect,url_for
import sys
import os
import re
import json
import datetime
import matplotlib.pyplot as plt
from urllib.parse import unquote

#sys.path.insert(0,os.path.abspath('services'))
# Create an instance of the Flask class that is the WSGI application.
# The first argument is the name of the application module or package,
# typically __name__ when using a single module.
TEMPLATE_DIR = os.path.abspath('templates')
STATIC_DIR = os.path.abspath('static')
FILES_DIR = os.path.abspath('files')
from services import Wikipedia_reader,Youtube_reader,DB_helper,My_DV
app = Flask(__name__,template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config['FILES_FOLDER'] = FILES_DIR

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
    wiki_output=mydb.exec_statement("select id,creation_date,search_text,title,url,description,thumbnail from Wikipedia order by search_text,title asc;")
    db_content={}
    for each in wiki_output:
        temp_dict={}
        '''
         make output based on search text
        '''
        search_text=each[2]
        if not db_content.get(search_text,None):
            db_content[search_text]={}
            db_content[search_text]['pages']=[]
        temp_dict['id']=each[0]
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
        #print(f"In main.py get_db function temp_dict is :\n {json.dumps(temp_dict,indent=2)}")
        db_content[search_text]['pages'].append(temp_dict)
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
    mydb=DB_helper()
    mydb.exec_statement("delete from Youtube;")
    mydb.exec_statement("delete from Wikipedia;")
    mydb.exec_statement("delete from view_counts;")
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
        '''
        for yt_each in yt_out:
            print(f"YOUTUBE OUT: {json.dumps(yt_each,indent=2)}")
        '''
        mydb.db_insert(table_name='Wikipedia',my_id=my_dict['id'],search_text=my_dict['search_text'],title=my_dict['title'],url=my_dict['url'],description=my_dict['description'],thumbnail=my_dict['thumbnail'])
    for each in mydb.alerts:
        print(f"Alert from DB_Helper: {each}")
    db_content=get_db()
    return render_template("wiki_search.html",db_content=db_content)
@app.route("/wiki_search")
def wiki_search():
    content=get_db()
    return render_template("wiki_search.html",db_content=content)

@app.route("/wiki_search_results",methods=['POST'])
def wiki_search_results():
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

@app.route('/add_view_count',methods=['POST'])
def add_view_count():
   # Render the page
   '''
   print(f"video id : {request.args.get('video_id')}  type: {request.args.get('type')}")
   '''
   mydb=DB_helper()
   mydb.db_insert(table_name='view_counts',my_id=request.args.get('video_id'),type=request.args.get('type'))
   return {'result':'success'}

@app.route('/delete_entry',methods=['POST'])
def delete_entry():
   # Render the page
   
   print(f"wiki id : {request.args.get('wiki_id')} ")
   print(f"youtube id : {request.args.get('youtube_id')} ")
   print(f"request : {request} ")
   
   mydb=DB_helper()
   wiki_id=request.args.get('wiki_id')
   youtube_id=request.args.get('youtube_id')
   if wiki_id:
       try:
           mydb.exec_statement("delete from view_counts where id = ? ;",wiki_id)
           mydb.exec_statement("delete from view_counts where id in (select id from Youtube where wiki_id = ? );",wiki_id)
           mydb.exec_statement("delete from Youtube where wiki_id = ? ;",wiki_id)
           mydb.exec_statement("delete from Wikipedia where id = ? ;",wiki_id)
       except Exception as e:
           print(f"Exception deleting wiki: {e}")
       for each_err in mydb.alerts:
           print(f"Error deleting: {each_err}")
   elif youtube_id:
       try:
           mydb.exec_statement("delete from view_counts where id = ? ;",youtube_id)
           mydb.exec_statement("delete from Youtube where id = ? ;",youtube_id)
       except Exception as e:
           print(f"Exception deleting youtube: {e}")
       for each_err in mydb.alerts:
           print(f"Error deleting: {each_err}")

   content=get_db()
   return render_template("wiki_search.html",db_content=content)

@app.route('/view_type_counts')
def view_type_counts():
    content={}
    mydv=My_DV()
    content['view_counts']=mydv.wiki_youtube_views()
    
    return render_template("data_analysis.html",content=content)
@app.route('/inventory_graph')
def inventory_graph():
    content={}
    mydv=My_DV()
    content['Wikipedia Inventory']=mydv.wiki_inventory_by_topic()
    
    return render_template("data_analysis.html",content=content)

@app.route('/views_by_topic')
def views_by_topic():
    content={}
    mydv=My_DV()
    content['Counts by Topic']=mydv.views_by_topic()
    
    return render_template("data_analysis.html",content=content)


@app.route('/')
@app.route('/index')
def index():
   # Render the page
   return render_template('index.html',debug=True)

if __name__ == '__main__':
   # Run the app server on localhost:4449
   app.run('localhost', 4449)

