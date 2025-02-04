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
from wordcloud import WordCloud, STOPWORDS

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

    def line_graph(self,x_list,y_list,title):
        plt.clf()
        plt.figure()
        graphs={}
        plt.title(title)
        plt.legend(loc='center left', bbox_to_anchor=(1,.5))
        plt.grid()
        img=io.BytesIO()
        
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')

        return graphs

class My_DV(DV_base):
    def __init__(self,*args,**kwargs):
        super(My_DV,self).__init__(*args,**kwargs)
        self.graphs={}
        self.mydb=DB_helper()
        self.graphs['errors']=[]

    def format_ts(self,in_ts):
        '''
        Function format_ts
    
        Parameters
        ----------
        in_ts : string
            Date string coming from the sqlite db
            Returns
        -------
        Formatted date to use with the matplotlib x-axis
        remove the year and add am/pm to it.
        '''
        temp_date = in_ts.split(':')[0][5:]
        hour=int(temp_date.split(' ')[1])
        if hour >= 12:
            my_date=temp_date[0:5] + '_' + str(hour) + '_pm'
        else:
            my_date=temp_date[0:5] + '_' + str(hour) + '_am'
             
        return my_date

    def build_views_dict(self):
        '''
         sql statement
        '''
        stmt="select b.search_text,b.title,strftime('%Y-%m-%d %H:%M',a.creation_date),a.type " \
            + "from view_counts a,Wikipedia b " \
            + "where b.id=a.id "\
            + "UNION " \
            + "select b.search_text,b.title,strftime('%Y-%m-%d %H:%M',a.creation_date),a.type " \
            + "from view_counts a, " \
            + "wikipedia b, " \
            + "youtube c " \
            + "where a.id=c.id " \
            + "and c.wiki_id=b.id " \
            + "order by 3 asc;"

        try:
            view_data = self.mydb.exec_statement(stmt)
        except Exception as e:
            return f"Exception getting view counts from db: {e}"
        my_dict = {}
        self.views_start=view_data[0][2]
        self.views_end=view_data[-1][2]
        self.all_view_dates=[]
        for each in view_data:
            my_search_text = each[0]
            my_title = each[1]
            #my_date = self.format_ts(each[2])
            my_date=each[2].split(':')[0]
            self.all_view_dates.append(my_date)
            my_type = each[3]
            
            if not my_dict.get(my_search_text, None):
                my_dict[my_search_text] = {}
                my_dict[my_search_text][my_type] = {}
                my_dict[my_search_text][my_type][my_title] = {}
                my_dict[my_search_text][my_type][my_title][my_date] = 0
            elif not my_dict[my_search_text].get(my_type,None):
                my_dict[my_search_text][my_type] = {}
                my_dict[my_search_text][my_type][my_title] = {}
                my_dict[my_search_text][my_type][my_title][my_date] = 0
            elif not my_dict[my_search_text][my_type].get(my_title,None):
                my_dict[my_search_text][my_type][my_title] = {}
                my_dict[my_search_text][my_type][my_title][my_date] = 0
            elif not my_dict[my_search_text][my_type][my_title].get(my_date,None):
                my_dict[my_search_text][my_type][my_title][my_date] = 0
            my_dict[my_search_text][my_type][my_title][my_date] += 1
        #print(f"MY DICT: {json.dumps(my_dict,indent=2)}")    
        
        return my_dict
        
    def views_by_topic(self):
        fig = plt.figure(figsize=(10,10))
        ax = fig.add_subplot(projection='3d')
        
        self.build_views_dict()
        '''
        now build the graph
        '''   
        zindex=0
        graph_dict={}
        views_dict=self.build_views_dict()
        for k,type_dict in views_dict.items():
            if not graph_dict.get(k,None):
                graph_dict[k]={}
                for eachd in sorted(set(self.all_view_dates)):
                    graph_dict[k][eachd]=0
                #print(f"Now we have these keys set:  {json.dumps(graph_dict[k],indent=2)}")
            for typek,title_dict in type_dict.items():
                for titlek,dates_dict in title_dict.items():
                    for datek,datev in dates_dict.items():
                        if not graph_dict[k].get(datek,None):
                            #print("DOUG!!Why did we get here?  these should be already pre-set to zero above")
                            #print(f"Missing date is {datek}  here's what I have: {graph_dict[k]}")
                            graph_dict[k][datek]=datev
                        else:
                            graph_dict[k][datek]+=datev
        try:
            for topic,dates in graph_dict.items():
                ax.bar([each for each,values in dates.items()],[value for each,value in dates.items()], zs=zindex, label=topic,zdir='y', alpha=0.8)
                zindex+=1
        except Exception as e:
            print(f"Exception: {e}")
        
        plt.title(f"Combined View Counts By Topic\n{self.views_start} - {self.views_end} ")
        
        ax.set_zlabel('View Counts')
        plt.xticks(rotation=90)
        ax.legend()
        
        img=io.BytesIO()
        graphs={}
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')

        return graphs

    def wiki_youtube_views(self):
        plt.clf()
        plt.figure(figsize=(10,10))
        graphs={}
        
        stmt='select type,strftime("%Y-%m-%d %H",creation_date),count(*) ' \
           + 'from view_counts ' \
           + ' group by 1,2 ' \
           + ' order by 2;'
           
        try:
            view_data=self.mydb.exec_statement(stmt)
        except Exception as e:
            print(f"Exception selecting from db: {e}")
        graph_dict={}
        start=view_data[0][1]
        end=view_data[-1][1]
        for each in view_data:
            my_type=each[0]
            my_date=each[1]
            my_count=each[2]
            if not graph_dict.get(my_date,None):
                graph_dict[my_date]={}
                graph_dict[my_date]['Youtube']=0
                graph_dict[my_date]['Wikipedia']=0
            if  my_type=='Youtube':
                graph_dict[my_date]['Youtube']=my_count
            elif my_type=='Wikipedia':
                graph_dict[my_date]['Wikipedia']=my_count
                
        #print(f"Graph dict is : {json.dumps(graph_dict,indent=2)}")
        
        marker='.'
        plt.plot(graph_dict.keys(),[v['Wikipedia'] for k,v in graph_dict.items()],label='Wikipedia',marker=marker)
        plt.plot(graph_dict.keys(),[v['Youtube'] for k,v in graph_dict.items()],label='Youtube',marker=marker)
       
        
        plt.title(f"Wikipedia/Youtube View Counts\n{start} - {end} ")
        plt.legend(loc='center left', bbox_to_anchor=(1,.5))
        plt.xticks(rotation=90)
        plt.grid()
        img=io.BytesIO()
        
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')
        graphs['title']="Wikipedia page/Youtube Video View Counts"

        return graphs

    def wiki_inventory_by_topic(self):
        plt.clf()
        plt.figure(figsize=(10,10))
        graphs={}
        stmt='select search_text,strftime("%Y-%m-%d",creation_date),count(*)' \
            +' from wikipedia group by 1 order by 2'
        try:
            view_data=self.mydb.exec_statement(stmt)
        except Exception as e:
            print(f"Exception selecting from db: {e}")
        fig, ax = plt.subplots()
        xs=[]
        ys=[]
        for each in view_data:
            xs.append(each[0])
            ys.append(each[2])
            ax.bar(each[0],each[2])
            
        ax.set_xticks([])

        ax.set_title('Wikipedia topic Inventory') 
        ax.legend(xs)
        img=io.BytesIO()
        
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')
        graphs['title']="Wikipedia page/Youtube Video View Counts"

        return graphs

    def views_wordcloud(self):
        comment_words = ''
        stopwords = set(STOPWORDS)
        stmt='select a.search_text,count(*) ' \
           + 'from wikipedia a,view_counts c '\
           + ' where a.id=c.id ' \
           + 'UNION ' \
           + 'select b.search_text,count(*) ' \
           + 'from youtube a,wikipedia b,view_counts c '\
           + 'where a.id=c.id '\
           + ' and a.wiki_id=b.id'\
           + ' group by 1 order by 1;'
        try:
            view_data=self.mydb.exec_statement(stmt)
        except Exception as e:
            print(f"Exception selecting from db: {e}")
            
        # split the value
        tokens=[]
        for each in view_data:
            token=each[0].replace(' ','')
            count=each[1]
            tokens.extend([token for i in range(count)])
        #print(f"Tokens are: {tokens}")
        stopwords = set(STOPWORDS)
     
        comment_words += " ".join(tokens)+" "
        wordcloud = WordCloud(width = 800, height = 800,
                background_color ='white',
                collocations=False,
                stopwords = stopwords,
                min_font_size = 10).generate(comment_words)
 
        # plot the WordCloud image 
        plt.title("WordCloud views by Topic")                    
        plt.figure(figsize = (8, 8), facecolor = None)
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.tight_layout(pad = 0)
        
        img=io.BytesIO()
        graphs={}
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')
        graphs['title']="Wordcloud views per Topic"

        return graphs

    def create_simple_one(self):
        plt.clf()
        plt.figure(figsize=(10,10))
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

if __name__ == '__main__':
    my_graph=My_DV()
    my_graph.create_simple_one()


