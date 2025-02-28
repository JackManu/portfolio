import sqlite3
import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta

class Portfolio_Base():
    """
    Portfolio_Base
    base class for this site
    as of now, just used to
    handle inserts of errors
    into the database.
    maybe site traffic stuff too
    """
    def __init__(self,db='DB/portfolio.db',cfg='cfg/.config',*args,**kwargs):
        self.db=db
        self.set_up_logging(log_level='error')
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
                raise Exception(e)

        '''
        Now the config file
        '''
        try:
            with open(cfg,'r') as cf:
                config=cf.read()
            self.config=json.loads(config)
        except FileNotFoundError as e:
            print(f"Config file not found, {cfg}.  {e}")
            raise Exception(e,f"Config file not found, {cfg}")
        except Exception as e:
            print(f"Other exception trying to open {cfg}: {e}")
            raise Exception(e,f"Other exception trying to open {cfg}")

    def set_up_logging(self,log_level="debug"):
        '''
        Function set_up_logging

        set up logging for all base classes
        '''
        self.logger=logging.getLogger(self.__class__.__name__)
        level_dict = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
        }
        self.logger.setLevel(level_dict[log_level])
        console_handler=logging.StreamHandler()
        console_handler.setLevel(level_dict[log_level])
        formatter=logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        return None

    def create_db(self):
        try:
            for each_script in self.config['DB_CREATION']:
                self.exec_statement(each_script)
        except sqlite3.Error as e:
            raise Exception(e,"In create_db")
        return None

    def db_insert(self,**kwargs):
        '''
        Insert based on input tablename/values
        '''
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
            elif kwargs['table_name']=='errors':
                print(f"Trying to insert into errors:  {kwargs}")
                cursor.execute("Insert or replace into errors (id,creation_date,type,module_name,error_text) values(null,?,?,?,?)",(my_date,str(kwargs['type']),str(kwargs['module_name']),str(kwargs['error_text'])))
            elif kwargs['table_name']=='comments':
                cursor.execute("Insert or replace into comments(id,creation_date,user_email,comment) values(null,?,?,?)",(my_date,kwargs['user_email'],kwargs['comment']))
            db.commit()
            db.close()
        except sqlite3.Error as e:
            raise Exception(e,f"db_insert with {kwargs}")

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
        except sqlite3.OperationalError as e:
            self.db_insert(table_name='errors',type='SQL',module_name=self.__class__.__name__,error_text=f'statement: {stmt} exception: {e}')
            raise Exception(e,f"Executing {stmt}")
        finally:
            db.close()
        return output

if __name__ == '__main__':
    print("Nothing here so far")


