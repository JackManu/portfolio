from ast import Try
import ast
from flask import Flask,render_template, request,redirect,url_for
import sys
import json
import os
import pusher
import datetime
import requests
import time

sys.path.insert(0,os.path.abspath('services'))
# Create an instance of the Flask class that is the WSGI application.
# The first argument is the name of the application module or package,
# typically __name__ when using a single module.

TEMPLATE_DIR = os.path.abspath('templates')
STATIC_DIR = os.path.abspath('static')
'''
for pythonanywhere deployment
TEMPLATE_DIR='/home/JackManu/portfolio/templates'
STATIC_DIR='/home/JackManu/portfolio/static'
'''
from services import Wikipedia_reader,Youtube_reader,My_DV,Pusher_handler
app = Flask(__name__,template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
def get_routes():
    routes_dict={}
    with app.test_request_context():
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            routes_dict[rule.endpoint]={}
            routes_dict[rule.endpoint]['rule']=rule.rule
            routes_dict[rule.endpoint]['methods']=methods

    return routes_dict

pusher=Pusher_handler()
@app.after_request
def after_request(response):
    if request.endpoint not in ['progress','static']:
        print(f"Endpoint {request.endpoint} was accessed with status code {response.status_code} sending event to pusher")
        try:
            pusher.send_event(request.endpoint)
        except Exception as e:
            print(f"Exception pushing event: {e.args}")

    return response

def get_db():
    '''
    Function get_db()

    Get entries from the portfolio db 
    Wikipedia and Youtube tables.
    format into json for use in html/jinja
    '''
    wiki=Wikipedia_reader()
    wiki_output=wiki.exec_statement("select id,creation_date,search_text,title,url,description,thumbnail from Wikipedia order by search_text,title asc;")
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
        yt_select=wiki.exec_statement("select id,creation_date,wiki_id,video_id,title,url,description,thumbnail from Youtube where wiki_id = ? order by title asc;",temp_dict['id'])
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
    wiki=Wikipedia_reader()
    wiki.exec_statement("delete from Youtube;")
    wiki.exec_statement("delete from Wikipedia;")
    wiki.exec_statement("delete from view_counts;")
    wiki.exec_statement("delete from errors;")
    db_content={}
    db_content['errors']=[]
    try:
        os.remove(os.path.abspath('DB/portfolio.db'))
    except Exception as e:
        db_content['errors'].append(f'Exception deleting ../DB/portfolio.db : {e}')
    return render_template("wiki_search.html",content=db_content)

@app.route("/wiki_insert",methods=['POST'])
def wiki_insert():
    wiki=Wikipedia_reader()
    db_content={}
    db_content['errors']=[]
    for k,v in request.form.items():
        my_dict=ast.literal_eval(v)
        youtube=Youtube_reader(f"{my_dict['title']} {my_dict['search_text']}",my_dict['id'])
        try:
            yt_out=youtube.load_db()
        except Exception as e:
            db_content['errors'].append(f"Exception inserting youtube data for {my_dict['search_text']}  title: {my_dict['title']}")
            db_content['errors'].append(f"Error from DB: {e}")
        if len(yt_out)==0:
            db_content['errors'].append(f"No youtube videos found for {my_dict['title']}.")
            db_content['errors'].append("Check the errors table for issues")
        try:
            wiki.db_insert(table_name='Wikipedia',my_id=my_dict['id'],search_text=my_dict['search_text'],title=my_dict['title'],url=my_dict['url'],description=my_dict['description'],thumbnail=my_dict['thumbnail'])
        except Exception as e:
            db_content['errors'].append(f"Exception inserting wikipedia data to db for {my_dict['search_text']}  title: {my_dict['title']}")
            db_content['errors'].append(f"Error from DB: {e.args}")
    db_content['db_data']=get_db()
    return render_template("wiki_search.html",content=db_content)

@app.route("/wiki_search",methods=['GET','POST'])
def wiki_search():
    content={}
    content['db_data']=get_db()
    content['SHOW_INTRO']=True
    #print(f"Before render search: {json.dumps(content,indent=2)}")
    return render_template("wiki_search.html",content=content)

@app.route("/wiki_search_results",methods=['POST'])
def wiki_search_results():
    content={}
    content['errors']=[]
    if request.method == 'POST':
        searchs=request.form.get('search_button','nothing')
        '''
        skip this if text is empty
        '''
        if len(searchs) > 0:
            cap_searchs=searchs[0].upper() + searchs[1:]
            num_pages=request.form.get('pages',5)
            search_wiki=Wikipedia_reader(cap_searchs,num_pages)
            try:
                content=search_wiki.get_pages()
            except Exception as e:
                content['errors'].append(f"Exception in wiki.get_pages in main.py \n{e}")
    
    return render_template("wiki_search_results.html",content=content)

@app.route('/add_view_count',methods=['GET','POST'])
def add_view_count():
   # Render the page
   
   #print(f"video id : {request.args.get('video_id')}  type: {request.args.get('type')}")
   
   wiki=Wikipedia_reader()
   try:
       wiki.db_insert(table_name='view_counts',my_id=request.args.get('video_id'),type=request.args.get('type'))
   except Exception as e:
       wiki.logger.error(f"Exception in wiki.db_insert to view_counts in main.py \n{e}")
   return {'result':'success'}

@app.route('/delete_entry',methods=['GET','POST'])
def delete_entry():
   # Render the page
   content={}
   content['errors']=[]
   wiki=Wikipedia_reader()
   wiki.logger.debug(f"  args: {request.args}")
   wiki.logger.debug(f"wiki id : {request.args.get('wiki_id')} ")
   wiki.logger.debug(f"youtube id : {request.args.get('yt_id')} ")
   wiki_id=request.args.get('wiki_id')
   youtube_id=request.args.get('yt_id')
   if wiki_id:
       try:
           wiki.exec_statement("delete from view_counts where id = ? ;",wiki_id)
       except Exception as e:
           content['errors'].append(f"Exception deleting view_counts for wiki: {e}")
       try:
           wiki.exec_statement("delete from view_counts where id in (select id from Youtube where wiki_id = ? );",wiki_id)
       except Exception as e:
           content['errors'].append(f"Exception deleting view_counts for youtube: {e}")
       try:
           wiki.exec_statement("delete from Youtube where wiki_id = ? ;",wiki_id)
       except Exception as e:
           content['errors'].append(f"Exception deleting wiki: {e}")
       try:
           wiki.exec_statement("delete from Wikipedia where id = ? ;",wiki_id)
       except Exception as e:
           content['errors'].append(f"Exception deleting wiki: {e}")
   elif youtube_id:
       try:
           wiki.exec_statement("delete from view_counts where id = ? ;",youtube_id)
       except Exception as e:
           content['errors'].append(f"Exception deleting view_counts: {e} {e.args}")
       try:
           wiki.exec_statement("delete from Youtube where id = ? ;",youtube_id)
       except Exception as e:
           content['errors'].append(f"Exception deleting youtube: {e} {e.args}")

   return {'result':'success'}

@app.route('/data_analysis',methods=['GET','POST'])
def data_analysis():
    START=datetime.datetime.now()
    mydv=My_DV()
    content={}
    db=get_db()
    content['topics']=db.keys()
    content['types']=list(mydv.graph_cfg.keys())
    content['graphs']={}
    content['videos']={}
    content['errors']=[]
    mydv.logger.debug(f"In data_analysis: {request.args}")
    graph=request.args.get('graph')
    mydv.logger.debug(f"Graph is {graph}")
    
    if graph:
        try:
            content['graphs'][graph]=mydv.make_graph(graph)
        except Exception as e:
            content['errors'].append(f" Exception creating {graph}")
            content['errors'].append(e.args)
        print(f"{graph} Started: {START} Ended: {datetime.datetime.now()}")

    return render_template("data_analysis.html",content=content)

@app.route('/blank')
def blank():
   # Render the page
   return render_template('blank.html',debug=True)

@app.route('/comments',methods=['GET','POST'])
def comments():
   # Render the page
   content={}
   content['errors']=[]
   '''
   use a wiki instance to do db stuff
   '''
   wiki=Wikipedia_reader()
   comment=request.form.get('comments',None)
   user_email=request.form.get('user_email','Anonymous')
   if comment:
       if len(user_email)==0:
           user_email='Anonymous'
       try:
           wiki.db_insert(table_name='comments',user_email=user_email,comment=comment)
       except Exception as e:
           try:
               wiki.db_insert(table_name='errors',type='SQL',module_name='main.py',error_text=f"Exception in wiki.db_insert to comments in main.py {e.args}")
           except Exception as e1:
               content['errors'].append(f"Something is seriously wrong with the DB in main.py \n{e1.args}")
           content['errors'].append(f"Exception in wiki.db_insert to 'comments' in main.py \n{e.args}")
   comments_db=wiki.exec_statement("select id,strftime('%Y-%m-%d %H:%M:%S',creation_date),user_email,comment from comments order by 1 desc;")     
   for each in comments_db:
       my_id=str(each[0])
       my_date=str(each[1])
       my_user=str(each[2])
       my_comment=str(each[3])
       content[my_id]={}
       content[my_id]['date']=my_date
       content[my_id]['user_email']=my_user
       content[my_id]['comment']=my_comment
   return render_template('comments.html',content=content)

@app.route('/site_traffic',methods=['GET','POST'])
def site_traffic():
    content={}
    pusher=Pusher_handler(routes=get_routes())
    try:
        content['data']=pusher.get_init_data()
    except Exception as e:
        print(f"Exception getting init data from site_traffic_init: {e}")
    #print(f"INIT DATA: {json.dumps(content['data'],indent=2)}")
    content['routes']=get_routes()
    content['errors']=[]

    return render_template('site_traffic.html',content=content)

@app.context_processor
def inject_global_vars():
    current_url = request.url
    curr_loc=os.path.dirname(os.path.abspath(__file__))
    if '\\' in curr_loc:
        print(f"Running on a local pc: {curr_loc}")
        base_uri='./'
    else:
        print(f"Running on pythonanywhere.com: {curr_loc}")
        base_uri=curr_loc
    with open(f'{base_uri}/cfg/.config','r') as cfg:
        config=ast.literal_eval(cfg.read())
    
    app_id=config['PUSHER']['connectivity']['app_id']
    app_key=config['PUSHER']['connectivity']['key']
    app_secret=config['PUSHER']['connectivity']['secret']
    app_cluster=config['PUSHER']['connectivity']['cluster']
    
    routes_dict=get_routes()
    with app.test_request_context():
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            routes_dict[rule.endpoint]={}
            routes_dict[rule.endpoint]['rule']=rule.rule
            routes_dict[rule.endpoint]['methods']=methods
    print(f"Current url: {current_url} base_uri: {base_uri}")
    return dict(base_uri=base_uri,routes=routes_dict,app_id=app_id,app_key=app_key,app_secret=app_secret,app_cluster=app_cluster)

@app.route('/progress',methods=['GET'])
def progress():

    def generate():
        for i in range(101):
            time.sleep(0.1)
            yield f"data:{i}\n\n"
    return app.response_class(generate(), mimetype='text/event-stream')

@app.route('/')
@app.route('/index')
def index():
   # Render the page
   return render_template('index.html',debug=True)

if __name__ == '__main__':
   # Run the app server on localhost:4449
   app.run('localhost', 4449)

