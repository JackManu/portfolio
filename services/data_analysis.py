"""
Created on Tue Dec 24 10:30:18 2024

@author: doug_
"""
from http.client import PARTIAL_CONTENT
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.lines import Line2D
import ast
from wordcloud import WordCloud, STOPWORDS
from portfolio_base import Portfolio_Base

'''
The following is needed to be able to
run plt in the background
to avoid that 'not in the main loop' failure
'''
plt.switch_backend('agg')
import random
import io
import base64

class DV_base(Portfolio_Base):
    def __init__(self,*args,**kwargs):
        super(DV_base,self).__init__(*args,**kwargs)
        plt.clf()
        plt.figure()
        self.graph_cfg=self.config['graph_cfg']

    def create_graph(self,videos={}):
        img=io.BytesIO()
        graphs={}
        graphs={}
        plt.savefig(img, format='png',
            bbox_inches='tight')
        img.seek(0)
        graphs['bytes']=base64.b64encode(img.getvalue()).decode('utf-8')
        graphs['videos']=videos
        return graphs

class My_DV(DV_base):
    def __init__(self,*args,**kwargs):
        super(My_DV,self).__init__(*args,**kwargs)
        self.graphs={}
        self.graphs['errors']=[]
        self.prune_view_counts()
        start_date,end_date=self.get_start_end_dates()
        self.start_date=start_date.split(' ')[0]
        self.end_date=end_date.split(' ')[0]
        self.color_idx=0
        self.colors=([element for index, element in enumerate(plt.get_cmap('tab10').colors)])
        self.colors.extend([element for index, element in enumerate(plt.get_cmap('viridis').colors) if index % 50 == 0])

    def get_color(self):
        my_color=self.colors[self.color_idx]
        self.color_idx+=1
        if self.color_idx > len(self.colors):
            self.color_idx=0

        return my_color

    def get_data(self,stmt):
        '''
        Parameters
        ----------
        stmt : String
            SQL to run on the database

        Raises
        ------
        Exception
            as much as possible from the db_helper.py module

        Returns
        -------
        view_data : data from view_counts table

        '''
        try:
            view_data = self.exec_statement(stmt)
        except Exception as e:
            self.logger.error(f"Exception: {e.args}")
            raise Exception(e,f"Exception getting view counts from db: {e.args} with statement: {stmt}")

        return view_data

    def get_start_end_dates(self):
        stmt="select min(strftime('%Y-%m-%d',creation_date)),max(strftime('%Y-%m-%d %H:%M:%S',creation_date)) " \
            + "from view_counts;"

        data=self.get_data(stmt)

        return data[0][0],data[0][1]

    def prune_view_counts(self):
        stmt="delete from view_counts where creation_date < date('now', '-7 days');"
        deleted_data=self.exec_statement(stmt)
        self.logger.info(f"Deleted rows from VIEW_COUNTS: {deleted_data}")
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
            if hour==0:
                hour=12
            my_date=temp_date[0:5] + '_' + str(hour) + '_am'

        return my_date

    def build_all_views_dict(self,time_granulation='hours'):
        '''
        Function: build_all_views_dict

        build a dictionary with all relevant information
        for every link that was viewed

        Parameters
        ----------
        time_granulation : TYPE, optional
            DESCRIPTION. The default is 'hours'.

        Returns
        -------
        None.

        '''

        stmt="select b.search_text,a.type,b.title as wikipedia_title,b.title as specific_title,b.id,b.url,strftime('%Y-%m-%d %H',a.creation_date),count(*) "\
            + "from view_counts a,Wikipedia b " \
            + "where b.id=a.id " \
            + "group by 1,2,3,4,5,6,7 " \
            + "UNION " \
            + "select b.search_text,a.type,b.title as wikipedia_title,c.title as specific_title,c.id,c.url,strftime('%Y-%m-%d %H',a.creation_date),count(*) " \
            + "from view_counts a, " \
            + " wikipedia b, " \
            + "youtube c " \
            + "where a.id=c.id "\
            + "and c.wiki_id=b.id " \
            + "group by 1,2,3,4,5,6,7 " \
            + "order by 7,1,3 asc;"

        view_data=self.get_data(stmt)
        views_dict={}
        for each in view_data:
            my_topic=each[0]
            my_type=each[1]
            my_wiki_title=each[2]
            my_spec_title=each[3]
            my_id=each[4]
            my_url=each[5]
            my_date=each[6]
            my_count=each[7]
            if not views_dict.get(my_topic,None):
                views_dict[my_topic]={}
                views_dict[my_topic][my_type]={}
                views_dict[my_topic][my_type][my_wiki_title]={}
                views_dict[my_topic][my_type][my_wiki_title][my_spec_title]={}
                views_dict[my_topic][my_type][my_wiki_title][my_spec_title][my_date]={}
            elif not views_dict[my_topic].get(my_type,None):
                views_dict[my_topic][my_type]={}
                views_dict[my_topic][my_type][my_wiki_title]={}
                views_dict[my_topic][my_type][my_wiki_title][my_spec_title]={}
                views_dict[my_topic][my_type][my_wiki_title][my_spec_title][my_date]={}
            elif not views_dict[my_topic][my_type].get(my_wiki_title,None):
                views_dict[my_topic][my_type][my_wiki_title]={}
                views_dict[my_topic][my_type][my_wiki_title][my_spec_title]={}
                views_dict[my_topic][my_type][my_wiki_title][my_spec_title][my_date]={}
            elif not views_dict[my_topic][my_type][my_wiki_title].get(my_spec_title,None):
                views_dict[my_topic][my_type][my_wiki_title][my_spec_title]={}
                views_dict[my_topic][my_type][my_wiki_title][my_spec_title][my_date]={}
            elif not views_dict[my_topic][my_type][my_wiki_title][my_spec_title].get(my_date,None):
                views_dict[my_topic][my_type][my_wiki_title][my_spec_title][my_date]={}

            views_dict[my_topic][my_type][my_wiki_title][my_spec_title][my_date]['url']=my_url
            views_dict[my_topic][my_type][my_wiki_title][my_spec_title][my_date]['count']=my_count
            views_dict[my_topic][my_type][my_wiki_title][my_spec_title][my_date]['id']=my_id
        self.logger.debug(f"All Views Dict: {json.dumps(views_dict,indent=2)}")
        return views_dict

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

        view_data=self.get_data(stmt)

        my_dict = {}
        self.all_view_dates=[]
        for each in view_data:
            my_search_text = each[0]
            my_title = each[1]
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
        self.logger.debug(f"MY DICT: {json.dumps(my_dict,indent=2)}")

        return my_dict
    '''
    graphs
    '''
    def make_graph(self,graph):
        '''
        Function make_graph

        .config has setting 'graph_types'
        key is the graph name, value is the function to run
        '''
        self.logger.debug(f"Trying to run: {str(getattr(self,self.graph_cfg[graph]))}")
        try:
            output=getattr(self,self.graph_cfg[graph])()
        except Exception as e:
            self.logger.error(f"Exception trying to run {self.graph_cfg[graph]}: {e}")
            raise Exception(e,f"Exception trying to run {self.graph_cfg[graph]}: {e}")

        return output

    def all_youtube_views(self,topic=None):
        plt.clf()
        graph_dict={}
        fig = plt.figure(figsize=(10,10))
        ax = fig.add_subplot()
        stmt="select b.search_text,strftime('%Y-%m-%d %H:%M:%S',a.creation_date),strftime('%s', a.creation_date) % 86400 as seconds,c.url,c.title,c.thumbnail,c.id" \
           + " from view_counts a,wikipedia b,youtube c " \
           + " where a.id=c.id "
        if topic: stmt += f" and b.search_text='{topic}'"
        stmt+=" and a.type='Youtube' " \
           + " and b.id=c.wiki_id " \
           + " order by 2,1 asc;"

        view_data=self.get_data(stmt)

        graph_dict={}
        legend_dict={}
        legend_dict['lines']=[]
        cindex=0
        videos_dict={}
        videos_idx=1
        graph_list=[]
        for each in view_data:
            my_topic=each[0]
            my_date=each[1]
            my_y=each[2]
            my_url=each[3]
            my_title=each[4]
            my_thumbnail=ast.literal_eval(each[5])
            my_video_id=each[6]

            if not legend_dict.get(my_topic,None):
                legend_dict[my_topic]={}
                cindex+=1
                my_color=self.get_color()
                legend_dict['lines'].append(Line2D([0], [0], color=my_color, lw=4))
                legend_dict[my_topic]['color']=my_color
            graph_list.append((my_topic,my_date,my_y,my_url,my_title,my_thumbnail,my_video_id))

        for each in graph_list:
            ax.scatter(each[1],each[2],label=each[1].split(' ')[0],marker='o',color=legend_dict[each[0]]['color'])
            ax.annotate(videos_idx,(each[1],each[2]),xytext=(each[1],each[2]+500))
            videos_dict[videos_idx]={}
            videos_dict[videos_idx]['date']=each[1]
            videos_dict[videos_idx]['url']=each[3]
            videos_dict[videos_idx]['title']=each[4]
            videos_dict[videos_idx]['thumbnail']=each[5]
            videos_dict[videos_idx]['id']=each[6]
            videos_idx+=1

        plt.title(f'Youtube viewing\n{self.start_date} - {self.end_date}')
        plt.xlabel('Dates')
        plt.ylabel('Times')
        plt.grid(True)
        prev_date='9999-99-99'
        new_labels=[]
        for tick in ax.get_xticklabels():
            tick.set_rotation(90)
            curr_text=tick.get_text().split(' ')[0]
            if curr_text == prev_date:
                new_labels.append('')
            else:
                new_labels.append(curr_text)
                prev_date=curr_text
        ax.set_xticklabels(new_labels)
        hours=['12am','1am','2am','3am','4am','5am','6am','7am','8am','9am', \
                    '10am','11am','12pm','1pm','2pm','3pm','4pm','5pm','6pm','7pm',\
                     '8pm','9pm','10pm','11pm']
        ax.set_yticks(range(0,86400,3600))
        ax.set_yticklabels(hours)

        plt.legend(legend_dict['lines'],list(ek for ek in legend_dict.keys() if ek !='lines'), loc='center left', bbox_to_anchor=(1,.5))

        return self.create_graph(videos=videos_dict)

    def bubble_by_topic(self):
        plt.clf()
        fig=plt.figure(figsize=(10,3))
        ax=fig.add_subplot()
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
        my_x=1
        for k,v in graph_dict.items():
            my_color=self.get_color()
            my_labels.append(k)
            my_count=graph_dict[k]['counts']
            custom_lines.append(Line2D([0], [0], color=my_color, lw=4))
            ax.scatter(my_x,1,s=int(my_count) * 60 ,label=k,color=my_color)
            ax.annotate(my_count,(my_x,1),va='center',ha='center',color='white')
            my_x+=1

        plt.title(f'Bubble views by Topic\n{self.start_date} - {self.end_date}')
        plt.xlabel('Topics')
        plt.grid(False)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        plt.xticks(rotation=90)
        plt.legend(custom_lines,my_labels, loc='center left', bbox_to_anchor=(1,.5))

        return self.create_graph()

    def bubble_by_type(self):
        plt.clf()
        plt.figure(figsize=(10,10))
        stmt="select type,strftime('%Y-%m-%d',creation_date),count(*) " \
           + " from view_counts group by 1,2 order by 2;"

        view_data=self.get_data(stmt)
        colors={"Wikipedia":"blue","Youtube":"red"}
        graph_dict={}
        for each in view_data:

            my_type=each[0]
            my_date=each[1]
            my_count=each[2]
            if not graph_dict.get(my_type,None):
                graph_dict[my_type]={}
                graph_dict[my_type][my_date]={}
                graph_dict[my_type][my_date]['count']=my_count
                graph_dict[my_type][my_date]['size']=(my_count * 5) * 20
            elif not graph_dict[my_type].get(my_date,None):
                graph_dict[my_type][my_date]={}
                graph_dict[my_type][my_date]['count']=my_count
                graph_dict[my_type][my_date]['size']=(my_count * 5) * 20
                '''
                handle situation for missing/zero counts for a type/date
                '''
                for k,v in graph_dict.items():
                    if not graph_dict[k].get(my_date,None):
                        graph_dict[k][my_date]={}
                        graph_dict[k][my_date]['count']=0
                        graph_dict[k][my_date]['size']=35
            else:
                graph_dict[my_type][my_date]['count']+=my_count
                graph_dict[my_type][my_date]['size']=(my_count * 5) * 20
        for k,v in graph_dict.items():
            xs=[each for each in sorted(graph_dict[k].keys())]
            ys=[edc['count'] for edk,edc in graph_dict[k].items()]
            ss=[edc['size'] for edk,edc in graph_dict[k].items()]
            plt.scatter(xs,ys,s=ss,label=k,color=colors[k])
            for x in range(len(xs)):
                plt.annotate(ys[x],(xs[x],ys[x]),va='center',ha='center',color='white')

        custom_lines = [Line2D([0], [0], color=colors['Wikipedia'], lw=4),
                Line2D([0], [0], color=colors['Youtube'], lw=4)]

        plt.title(f'Bubble views of Wikipedia/Youtube pages\n{self.start_date} - {self.end_date}')
        plt.xlabel('Dates')
        plt.grid(False)
        plt.ylabel('View Counts')
        plt.legend(custom_lines,['Wikipedia','Youtube'], loc='center left', bbox_to_anchor=(1,.5))
        plt.xticks(rotation=90)

        return self.create_graph()

    def views_by_topic(self):

        stmt="select b.search_text,strftime('%Y-%m-%d %H',a.creation_date),count(*) " \
            + "from view_counts a,Wikipedia b " \
            + "where b.id=a.id "\
            + " group by 1,2 " \
            + "UNION " \
            + "select b.search_text,strftime('%Y-%m-%d %H',a.creation_date),count(*) " \
            + "from view_counts a, " \
            + "wikipedia b, " \
            + "youtube c " \
            + "where a.id=c.id " \
            + "and c.wiki_id=b.id " \
            + "group by 1,2 " \
            + "order by 1,2;"

        view_data=self.get_data(stmt)

        graph_dict={}
        all_dates=sorted(set([each[1] for each in view_data]))

        self.logger.debug(f"All dates: {all_dates}")
        most=0
        for each in view_data:
            my_topic=each[0]
            my_date=each[1]
            my_count=each[2]
            if not graph_dict.get(my_topic,None):
                graph_dict[my_topic]={}
                for eachd in all_dates:
                    graph_dict[my_topic][eachd]=0
            graph_dict[my_topic][my_date]=my_count
            if my_count > most: most=my_count

        plt.clf()
        fig=plt.figure(figsize=(10,15))
        ax=fig.add_subplot(projection='3d')
        try:
            zindex=0
            yticks=[]
            yticklabels=[]
            for topic,dates in graph_dict.items():
                xs=[self.format_ts(each) for each,values in dates.items()]
                ys=[value if value>0 else 0 for each,value in dates.items()]
                ax.bar(xs,ys,zindex,label=topic,zdir='y', width=0.5,alpha=0.8,align='center',color=self.get_color())
                yticks.append(zindex)
                yticklabels.append(topic)
                zindex+=1
        except Exception as e:
            self.db_insert(table_name='errors',type='Matplotlib',module_name=self.__class__.__name__,error_text=f"{e.args}")
            self.logger.error(f"Exception: {e}")
            raise Exception(e)
        plt.title(f"Combined View Counts By Topic\n{self.start_date} - {self.end_date} ")
        ax.set_yticks([each for each in range(len(graph_dict.keys()))])
        ax.set_zlabel('View Counts')
        ax.set_zticks(range(most + 1))
        plt.xticks(rotation=90)
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

        view_data=self.get_data(stmt)
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

        self.logger.debug(f"Graph dict is : {json.dumps(graph_dict,indent=2)}")

        marker='.'
        plt.plot([self.format_ts(each) for each in graph_dict.keys()],[v['Wikipedia'] for k,v in graph_dict.items()],label='Wikipedia',color='blue',marker=marker)
        plt.plot([self.format_ts(each) for each in graph_dict.keys()],[v['Youtube'] for k,v in graph_dict.items()],label='Youtube',color='red',marker=marker)


        plt.title(f"Wikipedia/Youtube View Counts\n{self.start_date} - {self.end_date} ")
        plt.legend(loc='center left', bbox_to_anchor=(1,.5))
        plt.xticks(rotation=90)
        plt.grid()

        return self.create_graph()

    def wiki_inventory_by_topic(self):
        plt.clf()
        plt.figure(figsize = (10, 10))
        graphs={}
        stmt='select a.search_text,a.title,count(b.id) '\
           + 'from wikipedia a,youtube b ' \
           + 'where a.id=b.wiki_id '\
           + 'group by 1,2 '\
           + 'order by 1,2;'

        view_data=self.get_data(stmt)

        fig, ax = plt.subplots()
        xs=[]
        ys=[]
        custom_lines =[]
        labels=[]
        titles=[]
        graph_dict={}
        for each in view_data:
            my_label=each[0]
            my_title=each[1]
            yt_count=each[2]
            if not graph_dict.get(my_label,None):
                graph_dict[my_label]={}
                graph_dict[my_label]['color']=self.get_color()
                graph_dict[my_label]['titles']={}
            graph_dict[my_label]['titles'][my_title]=yt_count
            titles.append(my_title)

        self.logger.debug(f"Graph dict is: {json.dumps(graph_dict,indent=2)}")
        x=0
        for k,v in graph_dict.items():
            for title,count in v['titles'].items():
                ax.bar(title,count,width=0.5,color=v['color'])
                ax.annotate(count,(x,count + 1),va='center',ha='center',fontsize=8)
                x+=1

        # Add title and labels
        ax.set_title('Wikipedia/Youtube Inventory')
        plt.xticks(rotation=90)
        plt.legend([Line2D([0],[0],color=each['color'],lw=4) for k,each in graph_dict.items()],list(graph_dict.keys()), loc='center left', bbox_to_anchor=(1,.5))

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

        view_data=self.get_data(stmt)
        # split the value
        tokens=[]
        for each in view_data:
            token=each[0].replace(' ','')
            count=each[1]
            tokens.extend([token for i in range(count)])
        self.logger.debug(f"Tokens are: {tokens}")
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

    def show_colors(self):
        plt.clf()
        plt.figure(figsize=(10,10))
        x=0
        for each in self.colors:
            print(f"Color is: {each}")
            plt.bar(x,10,width=0.5,color=each)
            x+=1

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


