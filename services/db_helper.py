import sqlite3
from datetime import datetime, timezone, timedelta
import json
import os
import sys

class DB_helper():
    '''
    Class DB_helper

    open and/or create the sqlite database 'portfolio.db'
    '''
    def __init__(self,db='DB/portfolio.db',cfg='cfg/.config'):
        self.alerts=[]
        self.db=db
        if os.path.isfile(cfg):
            with open(cfg,'r') as cf:
                config=cf.read()
            self.config=json.loads(config)
        if not os.path.isfile(self.db) or os.stat(self.db).st_size == 0:
            with open(self.db,'w') as file:
                file.write('')
            file.close()
            try:
                self.create_db()
            except sqlite3.Error as e:
                self.alerts.append(f"Problem creating DB: {e}")
        
    def create_db(self):
        try:
            for each_script in self.config['DB_CREATION']:
                self.exec_statement(each_script)
        except sqlite3.Error as e:
            self.alerts.append(f"Problem executing create table statements: {e}")
            raise Exception(e)
        return None

    def db_insert(self,**kwargs):
        try:
            db=sqlite3.connect(self.db)
            '''
            Thank you stackoverflow!  
            pythonanywhere runs in GMT(I think..somewhere 7 or 8 hours ahead of me at least).
            setting this to do datetime.now() for pacific timezone
            '''
            timezone_offset = -8.0  # Pacific Standard Time (UTC−08:00)
            tzinfo = timezone(timedelta(hours=timezone_offset))
            my_date=datetime.now(tzinfo).strftime('%Y-%m-%d %H:%M:%S')
            cursor=db.cursor()
            if kwargs['table_name']=='Wikipedia':
                cursor.execute("Insert or replace into Wikipedia (id,creation_date,search_text,title,url,description,thumbnail) values(?,?,?,?,?,?,?)",(kwargs['my_id'],my_date,kwargs['search_text'],kwargs['title'],kwargs['url'],kwargs['description'],str(kwargs['thumbnail'])))
            elif kwargs['table_name']=='Youtube':
                cursor.execute("Insert or replace into Youtube (id,creation_date,wiki_id,video_id,title,url,description,thumbnail) values(?,?,?,?,?,?,?,?)",(kwargs['my_id'],my_date,kwargs['wiki_id'],kwargs['video_id'],kwargs['title'],kwargs['url'],kwargs['description'],str(kwargs['thumbnail'])))
            elif kwargs['table_name']=='view_counts':
                cursor.execute("Insert or replace into view_counts (id,creation_date,type) values(?,?,?)",(kwargs['my_id'],my_date,kwargs['type']))
            db.commit()
            db.close()
        except sqlite3.Error as e:
            self.alerts.append(f"Issue inserting:  {e}")
            raise Exception(e)

        return None

    def exec_statement(self,stmt,wiki_id=None):
        output=[]
        try:
            db=sqlite3.connect(self.db)
            cursor=db.cursor()
            if wiki_id:
                cursor.execute(stmt,[wiki_id])
            else:
                cursor.execute(stmt)
            output=cursor.fetchall()
            db.commit()
        except sqlite3.Error as e:
            raise Exception(e)
        finally:
            db.close()
        return output
    
if __name__ == '__main__':
    try:
        mydb=DB_helper("portfolio.db")
    except Exception as e:
        print(f"Exception opening db: {e}")
        sys.exit(1)
    for each in mydb.alerts:
        print(f"Alert: {each}")
        sys.exit(1)
    sel_stmt="select id,datetime(creation_date,'unixepoch'),search_text,title,url,description,thumbnail from Wikipedia order by creation_date desc;"
    
    table='Wikipedia'
    my_id=3
    title='trash'
    url='https://hello/how/are/you'
    desc='asdfasdf'
    thumbnail='somejpg'
    stmt=f"insert or ignore into {table} values({my_id},strftime('%s','now'),'{title}','{url}','{desc}','{thumbnail}')"
    output=mydb.insert(stmt,"portfolio.db")
    output=mydb.select(sel_stmt,"portfolio.db")
    for each in mydb.alerts:
        print(f"Alert: {each}")
    for each in output:
        print(f"Row: {each}")


