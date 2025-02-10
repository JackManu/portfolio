"""
Created on Tue Dec 24 10:30:18 2024

@author: doug_
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
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
        self.mydb=DB_helper()

    def create_graph(self):
        img=io.BytesIO()
        graphs={}
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')
        return graphs
    def line_graph(self,x_list,y_list,title):
        plt=self.start_graph()
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
        self.prune_view_counts()
        self.start_date,self.end_date=self.get_start_end_dates()
        cmap = plt.get_cmap('viridis')
        self.colors = [cmap(i/1000) for i in range(1,10001,20)]

    def get_start_end_dates(self):
        stmt="select min(strftime('%Y-%m-%d',creation_date)),max(strftime('%Y-%m-%d',creation_date)) " \
            + "from view_counts;"
        try:
            data=self.mydb.exec_statement(stmt)
        except Exception as e:
            print(f"Exception running statement: {e} {stmt}")
        
        return data[0][0],data[0][1]

    def prune_view_counts(self):
        stmt="delete from view_counts where creation_date < date('now', '-7 days');"
        deleted_data=self.mydb.exec_statement(stmt)
        print(f"Deleted rows from VIEW_COUNTS: {deleted_data}")
        return None

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
            if hour > 12: 
                hour-=12
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

    def bubble_by_topic(self):
        plt.clf()
        graph_dict={}
        custom_lines=[]
        my_labels=[]
        views_dict=self.build_views_dict()
        for k,v in views_dict.items():
            if not graph_dict.get(k,None):
                graph_dict[k]={}
                graph_dict[k]['counts']=0
            for typek,typev in v.items():
                for titlek,titlev in typev.items():
                    for datek,datev in titlev.items():
                        graph_dict[k]['counts']+=datev
        #print(f"Graphs dict: {json.dumps(graph_dict,indent=2)}")
        my_x=1
        for k,v in graph_dict.items():
            my_color=(random.random(), random.random(), random.random())
            #print(f"My color is : {my_color}")
            my_labels.append(k)
            my_count=graph_dict[k]['counts']
            custom_lines.append(Line2D([0], [0], color=my_color, lw=4))
            plt.scatter(my_x,1,s=int(my_count) * 50 ,label=k,color=my_color)
            plt.annotate(my_count,(my_x,1),xytext=(my_x - 7,-2),textcoords='offset points')
            my_x+=1
        #print(f"Before graph custom lines: {custom_lines} \n labels: {my_labels}")
        print(f" colors size: {len(self.colors)}")
        plt.title(f'Bubble views by Topic\n{self.start_date} - {self.end_date}')
        plt.xlabel('Topics')
        plt.grid(False)
        #plt.xticks([])
        #plt.yticks([])
        plt.xticks(rotation=90)
        plt.legend(custom_lines,my_labels, loc='center left', bbox_to_anchor=(1,.5))
        return self.create_graph()
                
    def bubble_by_type(self):
        plt.clf()
        plt.figure(figsize=(10,10))
        stmt="select type,strftime('%Y-%m-%d',creation_date),count(*) " \
           + " from view_counts group by 1,2 order by 1,2;"
        try:
            view_data = self.mydb.exec_statement(stmt)
        except Exception as e:
            return f"Exception getting view counts from db: {e}"
        graph_dict={}
        for each in view_data:
            
            my_type=each[0]
            my_date=each[1]
            my_count=each[2]
            if not graph_dict.get(my_type,None):
                graph_dict[my_type]={}
                graph_dict[my_type][my_date]={}
                graph_dict[my_type][my_date]['count']=my_count
                graph_dict[my_type][my_date]['size']=(my_count * 5) * 10
            elif not graph_dict[my_type].get(my_date,None):
                graph_dict[my_type][my_date]={}
                graph_dict[my_type][my_date]['count']=my_count
                graph_dict[my_type][my_date]['size']=(my_count * 5) * 10
            else:
                graph_dict[my_type][my_date]['count']+=my_count
                graph_dict[my_type][my_date]['size']=(my_count * 5) * 10
        colors=['blue','red']
        cx=0
        for k,v in graph_dict.items():
            xs=[each for each in graph_dict[k].keys()]
            ys=[edc['count'] for edk,edc in graph_dict[k].items()]
            ss=[edc['size'] for edk,edc in graph_dict[k].items()]
            plt.scatter(xs,ys,s=ss,label=k,color=colors[cx])
            cx+=1
        
        custom_lines = [Line2D([0], [0], color='blue', lw=4),
                Line2D([0], [0], color='red', lw=4)]

        plt.title(f'Bubble views of Wikipedia/Youtube pages\n{self.start_date} - {self.end_date}')
        plt.xlabel('Dates')
        plt.grid(False)
        plt.ylabel('View Counts')
        plt.legend(custom_lines,['Wikipedia','Youtube'], loc='center left', bbox_to_anchor=(1,.5))
        plt.xticks(rotation=90)
    
        return self.create_graph()

    def views_by_topic(self):
        plt.clf()
        fig=plt.figure(figsize=(10,10))
        ax=fig.add_subplot(projection='3d')
        
        self.build_views_dict()
        '''
        now build the graph
        '''   
        graph_dict={}
        views_dict=self.build_views_dict()
        for k,type_dict in views_dict.items():
            if not graph_dict.get(k,None):
                graph_dict[k]={}
                for eachd in sorted(set(self.all_view_dates)):
                    graph_dict[k][eachd]=0
                print(f"Now we have these keys set:  {json.dumps(graph_dict[k],indent=2)}")
            for typek,title_dict in type_dict.items():
                for titlek,dates_dict in title_dict.items():
                    for datek,datev in dates_dict.items():
                        if not graph_dict[k].get(datek,None):
                            print("DOUG!!Why did we get here?  these should be already pre-set to zero above")
                            print(f"Missing date is {datek}  here's what I have: {graph_dict[k]}")
                            graph_dict[k][datek]=datev
                        else:
                            graph_dict[k][datek]+=datev
        try:
            print(f"Data:  {json.dumps(graph_dict,indent=2)}")
            zindex=1
            for topic,dates in graph_dict.items():
                yticks=[]
                yticklabels=[]
                ax.bar([self.format_ts(each) for each,values in dates.items()],[value + 1 if value>0 else 0 for each,value in dates.items()], zs=zindex, label=topic,zdir='y', alpha=0.8)
                zindex+=1
                yticks.append(zindex)
                yticklabels.append(topic)
        except Exception as e:
            print(f"Exception: {e}")
        
        plt.title(f"Combined View Counts By Topic\n{self.start_date} - {self.end_date} ")
        
        ax.set_zlabel('View Counts')
        #ax.set_yticklabels([each for each in graph_dict.keys()])
        plt.xticks(rotation=90)
        #ax.set_yticks(yticks)
        #ax.set_yticklabels(yticklabels)
        ax.legend()

        return self.create_graph()

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
       
        
        plt.title(f"Wikipedia/Youtube View Counts\n{self.start_date} - {self.end_date} ")
        plt.legend(loc='center left', bbox_to_anchor=(1,.5))
        plt.xticks(rotation=90)
        plt.grid()

        return self.create_graph()

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
        
        return self.create_graph()

    def views_wordcloud(self):
        plt.clf()
        plt.figure(figsize=(10,10))
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
 
        plt.title("WordCloud views by Topic") 
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.tight_layout(pad = 0)

        return self.create_graph()

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

        return self.create_graph()

if __name__ == '__main__':
    my_graph=My_DV()
    my_graph.create_simple_one()


