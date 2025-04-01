from ast import Try
import ast
from flask import Flask,render_template, session,request,redirect,url_for,jsonify
import sys
import json
import os
import pusher
import datetime
import requests
import time
import re
from pathlib import Path

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
from services import Wikipedia_reader,Youtube_reader,My_DV,Pusher_handler,PortfolioException
app = Flask(__name__,template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
with open('./.flask_key.txt','r') as key:
       app.secret_key=key.readline()
key.close()

def get_routes():
    routes_dict={}
    with app.test_request_context():
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            if rule.endpoint not in ['progress','static','errors','delete_db','switch_db','static']:
                routes_dict[rule.endpoint]={}
                routes_dict[rule.endpoint]['rule']=rule.rule
                routes_dict[rule.endpoint]['methods']=methods

    return routes_dict

@app.after_request
def after_request(response):

    if request.endpoint not in ['progress','static','errors','switch_db','static']:
        pusher=Pusher_handler(db=session['site_db'],cfg=session['config'])
        print(f"Endpoint {request.endpoint} was accessed with status code {response.status_code} sending event to pusher")
        try:
            pusher.send_event(request.endpoint)
        except Exception as e:
            print(f"Exception pushing event: {e.args}")
        finally:
            del pusher

    return response

def get_keys():
    '''
    Function get_db()

    Get entries from the portfolio db 
    Wikipedia and Youtube tables.
    format into json for use in html/jinja
    '''
    START=datetime.datetime.now()
    wiki=Wikipedia_reader(db=session['curr_db'],cfg=session['config'])
    wiki_output=wiki.exec_statement(f"select distinct search_text from Wikipedia order by search_text;")
    db_content={f'{each[0]}':[] for each in wiki_output}
    print(f"Retrieve data in main.py get_keys started: {START} ended: {datetime.datetime.now()} ")
    return db_content

def get_db(db=None,topic=None):
    '''
    Function get_db()

    Get entries from the portfolio db 
    Wikipedia and Youtube tables.
    format into json for use in html/jinja
    '''
    START=datetime.datetime.now()

    db_content={}
    wiki=Wikipedia_reader(db=session['curr_db'],cfg=session['config'])
    if topic:
        stmt=f"select id,creation_date,search_text,title,url,description,thumbnail from Wikipedia where search_text='{topic}' order by search_text,title asc;"
    else:
        stmt=f"select id,creation_date,search_text,title,url,description,thumbnail from Wikipedia order by search_text,title asc;"
    
    wiki_output=wiki.exec_statement(stmt)
    
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
    print(f"Retrieve data in main.py get_db started: {START} ended: {datetime.datetime.now()} ")
    return db_content

@app.route("/aboutme")
def aboutme():
    content={}
    return render_template("aboutme.html",content=content)

@app.route("/aboutthis")
def aboutthis():
    content={}
    return render_template("aboutthis.html",content=content)

@app.route("/delete_db",methods=['POST'])
def delete_db(curr_db):
    wiki=Wikipedia_reader(db=curr_db,cfg=f"{session['base_uri']}/cfg/.config")
    wiki.exec_statement("delete from Youtube;")
    wiki.exec_statement("delete from Wikipedia;")
    wiki.exec_statement("delete from view_counts;")
    wiki.exec_statement("delete from errors;")
    db_content={}
    db_content['errors']=[]
    try:
        os.remove(os.path.abspath(session['curr_db']))
    except Exception as e:
        db_content['errors'].append(f'Exception deleting from {curr_db} : {e}')
    return render_template("wiki_search.html",content=db_content)

@app.route("/youtube_insert",methods=['POST'])
def youtube_insert():
    content={}
    wiki=Wikipedia_reader(db=session['curr_db'],cfg=session['config'])
    for k,v in request.form.items():
            my_dict=ast.literal_eval(v)
            wiki.db_insert(table_name='Youtube',my_id=my_dict['id'],wiki_id=my_dict['wiki_id'],title=my_dict['title'],url=my_dict['url'],description=my_dict['description'],thumbnail=my_dict['thumbnail'],video_id=my_dict['video_id'])
    content['db_data']=get_db(db=session['curr_db'])
    content['show_db_choice']=True
    return render_template("wiki_search.html",content=content)

@app.route("/wiki_insert",methods=['POST'])
def wiki_insert():
    print(f"Saving wiki entries to {session['curr_db']} cfg: {session['config']}  args: {request.args} form: {request.form}")
    wiki=Wikipedia_reader(db=session['curr_db'],cfg=session['config'])
    content={}
    content['errors']=[]
    content['show_db_choice']=True
   
    for k,v in request.form.items():
        my_dict=ast.literal_eval(v)
        t_nopunct=re.sub(r'[^A-Za-z0-9 ]+', '', my_dict['title'])
        s_nopunct=re.sub(r'[^A-Za-z0-9 ]+', '', my_dict['search_text'])
        print(f"Searching youtube for title: {t_nopunct} searcht: {s_nopunct}")
        youtube=Youtube_reader(f"{t_nopunct} {s_nopunct}",my_dict['id'],db=session['curr_db'],cfg=session['config'])
        try:
            yt_out=youtube.handle_db(insert=True)
        except Exception as e:
            content['errors'].append(f"Exception inserting youtube data for {s_nopunct}  title: {t_nopunct}")
            content['errors'].append(f"Error from DB: {e.args}")
        if len(yt_out)==0:
            content['errors'].append(f"No youtube videos found for {t_nopunct} {s_nopunct}")
            content['errors'].append("Check the errors table for issues")
        try:
            wiki.db_insert(table_name='Wikipedia',my_id=my_dict['id'],search_text=s_nopunct,title=t_nopunct,url=my_dict['url'],description=my_dict['description'],thumbnail=my_dict['thumbnail'])
        except Exception as e:
            content['errors'].append(f"Exception inserting wikipedia data to db for {s_nopunct}  title: {t_nopunct}")
            content['errors'].append(f"Error from DB: {e.args}")
    content['db_data']=get_db(db=session['curr_db'])
    return render_template("wiki_search.html",content=content)

@app.route("/wiki_search",methods=['GET','POST'])
def wiki_search():
    content={}
    content['errors']=[]
    content['show_db_choice']=True
    print(f"Curr db: {session['curr_db']} ")
    if 'portfolio.db' not in session['curr_db']:
        content['show_delete_db']=True
    else:
        print(f"show delete not set")

    print(f"Wiki search form is : {request.form} args: {request.args}")

    if request.form:
        if request.form.get('new_db',None):
            input_db=request.form.get('new_db','')
            new_db=re.sub(r'[^A-Za-z0-9 ]+', '',input_db)
            if len(new_db) > 0:
                session['curr_db']=f"{session['base_uri']}/DB/{new_db}.db"
                '''
                get the new db to be created
                '''
                try:
                    Wikipedia_reader(db=session['curr_db'],cfg=session['config'])
                except Exception as e:
                    print(f"Exception creating wikipedia_reader with new db: {e} ")
                    content['errors'].append(f"Exception creating wikipedia_reader with new db: {e} ")
        elif request.form.get('library_selection',None):
            curr_db=request.form.get('library_selection',None)
            session['curr_db']=f"{session['base_uri']}/DB/{curr_db}"
    
    content['db_data']=get_keys()

    print(f"In wiki_search curr db is : {session['curr_db']}  db_data: {content['db_data'].keys()}")

    return render_template("wiki_search.html",content=content)

@app.route("/view_topic",methods=['GET','POST'])
def view_topic():
    content={}
    if request.args.get('topic',None):
        print(f"Getting data for {request.args['topic']}")
        content['db_data']=get_db(topic=request.args['topic'])
    else:
        print(f"Nothing passed in")
    output=render_template('view_topic.html',content=content)
    #print(f"Before return output rendered is: {output}")
    return jsonify(html=output)

@app.route("/wiki_search_results",methods=['POST'])
def wiki_search_results():
    content={}
    content['errors']=[]
    content['show_db_choice']=True
    if 'portfolio.db' not in session['curr_db']:
        content['show_delete_db']=True

    #if request.method == 'POST':
    if request.args.get('youtube',None):
        #print(f"Youtube search request: {request.args}")
        my_yt_get=Youtube_reader(search_text=request.args['search_string'],max_results=50,wiki_id=request.args['wiki_id'],db=session['curr_db'],cfg=session['config'])
        try:
            content=my_yt_get.handle_db(insert=False)
        except Exception as e:
            content['errors'].append(f'Error getting youtube videos: {e}')
        return render_template("youtube_search_results.html",content=content)
    else:
        #print(f"Wikipedia search request: {request.args}")
        searchs=request.form.get('search_button',None)
        if not searchs:
            searchs=request.args.get('search_string','Not_Found')

        '''
        skip this if text is empty
        '''
        if len(searchs) > 0:
            cap_searchs=searchs[0].upper() + searchs[1:]
            ss_no_punctuation=re.sub(r'[^A-Za-z0-9 ]+', '', cap_searchs)
            num_pages=request.form.get('pages',50)
            search_wiki=Wikipedia_reader(ss_no_punctuation,num_pages,db=session['curr_db'],cfg=session['config'])
            try:
                content=search_wiki.get_pages()
            except Exception as e:
                content['errors'].append(f"Exception in wiki.get_pages in main.py \n{e}")
    
        return render_template("wiki_search_results.html",content=content)

@app.route('/add_view_count',methods=['GET','POST'])
def add_view_count():
   # Render the page
   
   print(f"video id : {request.args.get('video_id')}  type: {request.args.get('type')} db: {session['curr_db']}")
   
   wiki=Wikipedia_reader(db=session['curr_db'],cfg=session['config'])
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
   wiki=Wikipedia_reader(db=session['curr_db'],cfg=session['config'])
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

'''
@app.route('/switch_db',methods=['GET','POST'])
def switch_db():
    db_choice=request.form.get('library_selection',None)
    if db_choice: 
        session['curr_db']=f"{session['base_uri']}/DB/{db_choice}"
    return None
'''

@app.route('/data_analysis',methods=['GET','POST'])
def data_analysis():
    print(f"Datanalysis with db: {session['curr_db']}")
    graph=request.args.get('graph',None)
    db_choice=request.form.get('library_selection',None)
    if db_choice: 
        session['curr_db']=f"{session['base_uri']}/DB/{db_choice}"

    START=datetime.datetime.now()
    mydv=My_DV(db=session['curr_db'],cfg=session['config'])
    content={}
    db=get_db(db=session['curr_db'])
    content['topics']=db.keys()
    content['types']=list(mydv.graph_cfg.keys())
    content['graphs']={}
    content['videos']={}
    content['errors']=[]
    mydv.logger.debug(f"In data_analysis: {request.args} form: {request.form}")
    
    if graph:
        try:
            content['graphs'][graph]=mydv.make_graph(graph)
            if len(content['graphs'][graph])==0:
                content['errors']='No Data Found'
        except PortfolioException as p:
            del content['graphs']
            content['no_data']=f"No Data found for {graph}"
        
        print(f"{graph} Started: {START} Ended: {datetime.datetime.now()}")

    return render_template("data_analysis.html",content=content)

@app.route('/blank')
def blank():
   content={}
   # Render the page
   return render_template('blank.html',content=content)

@app.route('/comments',methods=['GET','POST'])
def comments():
   # Render the page
   content={}
   content['errors']=[]
   wiki=Wikipedia_reader(db=session['site_db'],cfg=session['config'])
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
    pusher=Pusher_handler(routes=get_routes(),db=session['site_db'],cfg=session['config'])
    try:
        content['data']=pusher.get_init_data()
    except Exception as e:
        print(f"Exception getting init data from site_traffic_init: {e}")
    #print(f"INIT DATA: {json.dumps(content,indent=2)}")
    content['routes']=get_routes()
    content['errors']=[]

    return render_template('site_traffic.html',content=content)

@app.route('/errors',methods=['GET','POST'])
def errors():
    content={}
    mydv=My_DV(db=session['site_db'],cfg=session['config'])
    stmt='select id,creation_date,type,module_name,error_text from errors order by id;'
    try:
        db_errors=mydv.exec_statement(stmt)
    except Exception as e:
        content['errors'].append(f"Error retrieving from ")
    content['db_errors']=[]
    for each in db_errors:
        content['db_errors'].append({'id':each[0],'date':each[1],'type':each[2],'module_name':each[3],'error_text':each[4]})
    return render_template('errors.html',content=content)

def get_base_uri():
    curr_loc=os.path.dirname(os.path.abspath(__file__))
    if '\\' in curr_loc:
        print(f"Running on a local pc: {curr_loc}")
        base_uri='./'
    else:
        print(f"Running on pythonanywhere.com: {curr_loc}")
        base_uri=curr_loc
    return base_uri

@app.context_processor
def inject_global_vars():
    base_uri=get_base_uri()
    session['base_uri']=base_uri
    session['config']=f'{base_uri}/cfg/.config'

    current_url = request.url
    with open(session["config"],'r') as cfg:
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
    databases=[Path(f).as_posix() for f in sorted(os.listdir(f'{base_uri}/DB/')) if f.__contains__('.db') and f !='site.db']
    session['site_db']=f'{base_uri}/DB/site.db'
    print(f"Databases: {databases}")
    return dict(databases=databases,base_uri=base_uri,routes=routes_dict,app_id=app_id,app_key=app_key,app_secret=app_secret,app_cluster=app_cluster)

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
   content={}
   session['curr_db']=f'{get_base_uri()}/DB/portfolio.db'
   return render_template('index.html',content=content)

if __name__ == '__main__':
   # Run the app server on localhost:4449
   app.run('localhost', 4449)

