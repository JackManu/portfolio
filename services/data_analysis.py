"""
Created on Tue Dec 24 10:30:18 2024

@author: doug_
"""
from datetime import datetime
import os
import math
import json
import sys
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
'''
The following is needed to be able to
run plt in the background
to avoid that 'not in the main loop' failure
'''
plt.switch_backend('agg')
import random
import io
import base64
from db_helper import DB_helper

class DV_base(object):
    def __init__(self,*args,**kwargs):
        plt.clf()
        plt.figure()
    def line_graph(self,x_list,y_list):
        pass
    def get_date_range_list(self,db_output): 
        '''
        function get_date_range_list

        assuming the date is the second element in the db_output list
        return a list for proper increments
        '''

        date_range_list=[each[1].split('.')[0].split(' ')[0] for each in db_output]
        print(f"Input dates: {date_range_list}")
        '''
        how many days do we have?
        '''
        if len(set(date_range_list)) < 3:
            '''
            just return a list with date/hours
            nevermind,  this is probably a stupid idea
            '''
        else:
            return date_range_list

class My_DV(DV_base):
    def __init__(self,*args,**kwargs):
        super(My_DV,self).__init__(*args,**kwargs)
        self.graphs={}
        self.mydb=DB_helper()
        self.graphs['errors']=[]
    def create_simple_one(self):
        plt.clf()
        plt.figure()
        mydict={'Cool Stuff':[],'Lame Stuff':[],'Fun Stuff':[],'Sad Stuff':[]}

        x_points=np.array(['01-01','01-02','01-03','01-04','01-05','01-06','01-07','01-08','01-09','01-10'])
        for each in range(10):
            for k,v in mydict.items():
                v.append(random.randint(1,1000))
        marker='.'
        for k,v in mydict.items():
            plt.plot(x_points,np.array(v),label=k,marker=marker)

        plt.title(f"Stuff that happened\n{x_points[0]}-2025 - {x_points[-1]}-2025")
        plt.legend(loc='center left', bbox_to_anchor=(1,.5))
        plt.grid()
        #plt.show()
   

        img=io.BytesIO()
        '''
        try:
            plt.savefig(os.path.join('files','simple_one.png'))
        except Exception as e:
            self.graphs['errors'].append(f" Error saving simple_one: {e}")
        '''
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        self.graphs={}
        self.graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')
        self.graphs['title']="Simple/Fake one.  proof of concept"

        return self.graphs

    def insert_history(self):
        plt.clf()
        plt.figure()
        graphs={}
        mydict={'Wikipedia':{},'Youtube':{}}
        stmt='select a.title,a.creation_date,"Wikipedia" ' \
            + 'from wikipedia a ' \
            + 'union ' \
            + 'select a.title,a.creation_date,"Youtube" ' \
            + 'from youtube a ' \
            + 'order by a.creation_date asc;'

        try:
            view_data=self.mydb.exec_statement(stmt)
        except Exception as e:
            print(f"Exception selecting from db: {e}")

        for each in view_data:
            #print(f"View data: {each}")
            time_str=''.join(each[1].split(':')[0:-2])
            hour=int(time_str[-3:])
            #print(f"last two of time_str: {hour}")
            if hour >= 12:
                new_hour=hour - 12
                new_ts=time_str.split(' ')[0] + f"_{new_hour}_pm"
            else:
                if hour==0: hour=12
                new_ts=time_str.split(' ')[0] + f"_{hour}_am"

            my_title=each[0]
            my_type=each[2]
            if my_type=='Wikipedia':
                if not mydict[my_type].get(new_ts,None):
                    mydict[my_type][new_ts]=[]
                mydict[my_type][new_ts].append(my_title)
                if not mydict['Youtube'].get(new_ts,None):
                    mydict['Youtube'][new_ts]=[]
            if my_type=='Youtube':
                if not mydict[my_type].get(new_ts,None):
                    mydict[my_type][new_ts]=[]
                mydict[my_type][new_ts].append(my_title)
                if not mydict['Wikipedia'].get(new_ts,None):
                    mydict['Wikipedia'][new_ts]=[]

            #print(f"Type: {my_type} title: {my_title} Time str: {new_ts}")
            
                    
        x_points=mydict['Wikipedia'].keys()
        marker='.'
        temp_array=[]
        for k,v in mydict.items():
            for innerk,innerv in v.items():
                #print(f"innerk is a {type(innerk)} {innerk} innerv is a {type(innerv)} {innerv}")
                temp_array.append(len(innerv))
            #print(f"Populated {k} array with: {temp_array}")
            plt.xticks(range(len(x_points)), x_points, rotation='vertical')
            plt.plot(x_points,np.array(temp_array),label=k,marker=marker)
            temp_array=[]
        
        plt.title(f"Wikipedia page/Youtube Video Inserts")
        plt.legend(loc='center left', bbox_to_anchor=(1,.5))
        plt.grid()
        img=io.BytesIO()
        
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')

        return graphs
    def views_by_topic(self):
    def insert_history(self):
        plt.clf()
        plt.figure()
        graphs={}
        mydict={'views':{}}
        stmt='select a.title,a.creation_date,"Wikipedia" ' \
            + 'from wikipedia a ' \
            + 'union ' \
            + 'select a.title,a.creation_date,"Youtube" ' \
            + 'from youtube a ' \
            + 'order by a.creation_date asc;'

        try:
            view_data=self.mydb.exec_statement(stmt)
        except Exception as e:
            print(f"Exception selecting from db: {e}")

        for each in view_data:
            #print(f"View data: {each}")
            time_str=''.join(each[1].split(':')[0:-2])
            hour=int(time_str[-3:])
            #print(f"last two of time_str: {hour}")
            if hour >= 12:
                new_hour=hour - 12
                new_ts=time_str.split(' ')[0] + f"_{new_hour}_pm"
            else:
                if hour==0: hour=12
                new_ts=time_str.split(' ')[0] + f"_{hour}_am"

            my_title=each[0]
            my_type=each[2]
            if my_type=='Wikipedia':
                if not mydict[my_type].get(new_ts,None):
                    mydict[my_type][new_ts]=[]
                mydict[my_type][new_ts].append(my_title)
                if not mydict['Youtube'].get(new_ts,None):
                    mydict['Youtube'][new_ts]=[]
            if my_type=='Youtube':
                if not mydict[my_type].get(new_ts,None):
                    mydict[my_type][new_ts]=[]
                mydict[my_type][new_ts].append(my_title)
                if not mydict['Wikipedia'].get(new_ts,None):
                    mydict['Wikipedia'][new_ts]=[]

            #print(f"Type: {my_type} title: {my_title} Time str: {new_ts}")
            
                    
        x_points=mydict['Wikipedia'].keys()
        marker='.'
        temp_array=[]
        for k,v in mydict.items():
            for innerk,innerv in v.items():
                #print(f"innerk is a {type(innerk)} {innerk} innerv is a {type(innerv)} {innerv}")
                temp_array.append(len(innerv))
            #print(f"Populated {k} array with: {temp_array}")
            plt.xticks(range(len(x_points)), x_points, rotation='vertical')
            plt.plot(x_points,np.array(temp_array),label=k,marker=marker)
            temp_array=[]
        
        plt.title(f"Views by Wikipedia topic")
        plt.legend(loc='center left', bbox_to_anchor=(1,.5))
        plt.grid()
        img=io.BytesIO()
        
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')

        return graphs
    def create_view_counts(self):
        plt.clf()
        plt.figure()
        graphs={}
        mydict={'Wikipedia':{},'Youtube':{}}
        stmt='select a.title,b.creation_date,b.type ' \
            + 'from wikipedia a,view_counts b ' \
            + 'where a.id=b.id '\
            + 'UNION ALL '\
            + 'select a.title,b.creation_date,b.type '\
            + 'from youtube a,view_counts b '\
            + 'where a.id=b.id order by b.creation_date asc;'
        view_data=self.mydb.exec_statement(stmt)
        for each in view_data:
            #print(f"View data: {each}")
            
            time_str=''.join(each[1].split(':')[0:-2])
            hour=int(time_str[-3:])
            if hour >= 12:
                new_hour=hour - 12
                new_ts=time_str.split(' ')[0] + f"_{new_hour}_pm"
            else:
                if hour==0: hour=12
                new_ts=time_str.split(' ')[0] + f"_{hour}_am"
            my_type=each[2]
            my_title=each[0]
            #print(f"Type: {my_type} title: {my_title} Time str: {time_str}")
            if my_type=='Youtube':
                if mydict['Youtube'].get(new_ts,None):
                    mydict['Youtube'][new_ts]+=1
                else:
                    mydict['Youtube'][new_ts]=1
                if not mydict['Wikipedia'].get(new_ts,None):
                    mydict['Wikipedia'][new_ts]=0          
            elif my_type=='Wikipedia':
                if mydict['Wikipedia'].get(new_ts,None):
                    mydict['Wikipedia'][new_ts]+=1
                else:
                    mydict['Wikipedia'][new_ts]=1
                if not mydict['Youtube'].get(new_ts,None):
                    mydict['Youtube'][new_ts]=0
                    
        x_points=mydict['Wikipedia'].keys()
        marker='.'
        temp_array=[]
        for k,v in mydict.items():
            for innerk,innerv in v.items():
                print(f"innerk is a {type(innerk)} {innerk} innerv is a {type(innerv)} {innerv}")
                temp_array.append(innerv)
            print(f"Populated {k} array with: {temp_array}")
            plt.xticks(range(len(x_points)), x_points, rotation='vertical')
            plt.plot(x_points,np.array(temp_array),label=k,marker=marker)
            temp_array=[]
        
        plt.title(f"Wikipedia page/Youtube Video View Counts ")
        plt.legend(loc='center left', bbox_to_anchor=(1,.5))
        plt.grid()
        img=io.BytesIO()
        
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')
        graphs['title']="Wikipedia page/Youtube Video View Counts"

        return graphs
if __name__ == '__main__':
    my_graph=My_DV()
    my_graph.create_simple_one()


