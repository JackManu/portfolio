import sqlite3
import datetime
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
            self.exec_statement(self.config['db_create_wikipedia'])
            self.exec_statement(self.config['db_create_wikipedia'])
        except sqlite3.Error as e:
            self.alerts.append(f"Problem executing create table statements: {e}")
        return None
    def db_insert(self,table_name,my_id,title,url,description,thumbnail):
        try:
            db=sqlite3.connect(self.db)
            cursor=db.cursor()
            cursor.execute(f"Insert or replace into {table_name} (id,creation_date,title,url,description,thumbnail) values(?,?,?,?,?,?)",(my_id,datetime.datetime.now(),title,url,description,str(thumbnail)))
            db.commit()
            db.close()
        except sqlite3.Error as e:
            self.alerts.append(f"Issue inserting:  {e}")
        return None

    def exec_statement(self,stmt):
        output=[]
        try:
            db=sqlite3.connect(self.db)
            cursor=db.cursor()
            cursor.execute(stmt)
            output=cursor.fetchall()
            db.commit()
        except sqlite3.Error as e:
            self.alerts.append(f'Problem executing {stmt} \n {e}') 
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
    sel_stmt="select id,datetime(creation_date,'unixepoch'),title,url,description,thumbnail from Wikipedia order by creation_date desc;"
    
    table='Wikipedia'
    my_id=3
    title='trash'
    url='https://fuck_you/tgo/hell'
    desc='asdfasdf'
    thumbnail='somejpg'
    stmt=f"insert or ignore into {table} values({my_id},strftime('%s','now'),'{title}','{url}','{desc}','{thumbnail}')"
    output=mydb.insert(stmt,"portfolio.db")
    output=mydb.select(sel_stmt,"portfolio.db")
    for each in mydb.alerts:
        print(f"Alert: {each}")
    for each in output:
        print(f"Row: {each}")


