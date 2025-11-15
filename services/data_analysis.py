"""
Created on Tue Dec 24 10:30:18 2024

@author: doug_
"""
from http.client import PARTIAL_CONTENT
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
mplstyle.use('fast')
from datetime import datetime
from matplotlib.lines import Line2D
import ast
import math
import matplotlib.gridspec as gridspec
from wordcloud import WordCloud, STOPWORDS
from portfolio_base import Portfolio_Base,PortfolioException
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

    def __del__(self):
        plt.close()
               

class My_DV(DV_base):
    def __init__(self,*args,**kwargs):
        super(My_DV,self).__init__(*args,**kwargs)
        
        self.graphs={}
        self.graphs['errors']=[]
        #self.prune_view_counts()
        self.color_idx=0
        self.colors=([element for index, element in enumerate(plt.get_cmap('tab10').colors)])
        self.colors.extend([element for index, element in enumerate(plt.get_cmap('viridis').colors) if index % 50 == 0])
        if kwargs.get('db_list',None):
            self.db_list=kwargs['db_list']

    def get_color(self):
        my_color=self.colors[self.color_idx]
        self.color_idx+=1
        if self.color_idx >= len(self.colors):
            self.color_idx=0

        return my_color

    def get_data(self,stmt,ignore_empty=False):
        '''
        Parameters
        ----------
        stmt : String
            SQL to run on the database

        Raises
        ------
        Exception
            raises PortfolioException if no data found

        Returns
        -------
        view_data : data from view_counts table

        '''
        try:
            view_data = self.exec_statement(stmt)
        except Exception as e:
            self.logger.error(f"Exception: {e.args}")
            raise Exception(e,f"Exception getting view counts from db: {e.args} with statement: {stmt}")

        if len(view_data) == 0 and not ignore_empty:
            raise PortfolioException('No Data Found',999)
        else:
            return view_data

    def get_start_end_dates(self):
        stmt="select min(strftime('%Y-%m-%d',creation_date)),max(strftime('%Y-%m-%d',creation_date)) " \
            + "from view_counts;"

        data=self.get_data(stmt)
        return data[0][0],data[0][1]

    def prune_view_counts(self):
        stmt="delete from view_counts where creation_date < date('now', '-14 days');"
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
       
        output=getattr(self,self.graph_cfg[graph])()

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
        start_date=view_data[0][1]
        end_date=view_data[-1][1]
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

        
        fig = plt.figure(figsize=(12,8))
        ax = fig.add_subplot()

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

        plt.title(f'Youtube viewing for {self.db.split("/")[-1]}\n{start_date} - {end_date}')
        plt.xlabel('Dates')
        plt.ylabel('Times')
        plt.xlim(0,len(graph_list))
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
                     '8pm','9pm','10pm','11pm','12am']
        ax.set_yticks(range(0,86401,3600))
        ax.set_yticklabels(hours)

        plt.legend(legend_dict['lines'],list(ek for ek in legend_dict.keys() if ek !='lines'), loc='center left', bbox_to_anchor=(1,.5))
        
        return self.create_graph(videos=videos_dict)

    def bubble_by_type(self):
        plt.clf()
        plt.figure(figsize=(10,10))
        stmt="select type,strftime('%Y-%m-%d',creation_date),count(*) " \
           + " from view_counts group by 1,2 order by 2;"

        view_data=self.get_data(stmt)

        colors={"Wikipedia":"blue","Youtube":"red"}
        graph_dict={}
        start_date=view_data[0][1]
        end_date=view_data[-1][1]
        highest=0
        for each in view_data:

            my_type=each[0]
            my_date=each[1]
            my_count=each[2]
            if my_count>highest:highest=my_count
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
            plt.scatter(xs,ys,s=ss,label=k,alpha=0.8,color=colors[k])
            for x in range(len(xs)):
                plt.annotate(ys[x],(xs[x],ys[x]),va='center',ha='center',color='white')

        custom_lines = [Line2D([0], [0], color=colors['Wikipedia'], lw=4),
                Line2D([0], [0], color=colors['Youtube'], lw=4)]

        plt.title(f'Bubble views of Wikipedia/Youtube pages for {self.db.split("/")[-1]}\n{start_date} - {end_date}')
        plt.xlabel('Dates')
        plt.grid(False)
        plt.ylabel('View Counts')
        plt.legend(custom_lines,['Wikipedia','Youtube'], loc='center left', bbox_to_anchor=(1,.5))
        plt.xticks(rotation=90)
        plt.yticks(range(0,highest + 1))

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
        if len(all_dates) > 0 :
            plt.title(f"Combined View Counts By Topic for {self.db.split('/')[-1]}\n{all_dates[0]} - {all_dates[-1]} ")
        else:
            plt.title(f"Combined View Counts By Topic for {self.db.split('/')[-1]}\n No Data Found ")

        
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
        start_date=view_data[0][1]
        end_date=view_data[-1][1]
        highest=0
        for each in view_data:
            my_type=each[0]
            my_date=each[1]
            my_count=each[2]
            if my_count> highest: highest=my_count
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
        plt.plot([self.format_ts(each) for each in graph_dict.keys()],[v['Wikipedia'] for k,v in graph_dict.items()],label='Wikipedia',color='blue',alpha=0.8,marker=marker)
        plt.plot([self.format_ts(each) for each in graph_dict.keys()],[v['Youtube'] for k,v in graph_dict.items()],label='Youtube',color='red',alpha=0.8,marker=marker)


        plt.title(f"Wikipedia/Youtube View Counts for {self.db.split('/')[-1]}\n{start_date} - {end_date} ")
        plt.legend(loc='center left', bbox_to_anchor=(1,.5))
        plt.xticks(rotation=30)
        plt.yticks(range(0,highest + 1))
        plt.grid()

        return self.create_graph()

    def get_bubble_top(self,y_coord, size):
        radius = np.sqrt(size) / 2  # Radius in points
        radius_in_data_units = radius / 72  # Convert points to inches (assuming 72 points per inch)
        top_y = y_coord + radius_in_data_units
        return top_y

    def viewing_habits(self):
        plt.clf()
        
        center_x, center_y = 0,0
        radius=1
        graph_dict={}
        '''
        Get Data
        '''
        for each_db in self.db_list:
            self.db=each_db
            stmt='select a.search_text,count(*) ' \
            + ' from wikipedia a,view_counts b,youtube c ' \
            + ' where b.id=c.id and a.id=c.wiki_id ' \
            + ' group by 1 order by 2 desc;'
            data=self.get_data(stmt,ignore_empty=True)
            for each in data:
                if not graph_dict.get(each_db,None):
                    graph_dict[each_db]={}
                    graph_dict[each_db]['topics']={}
                    graph_dict[each_db]['name']=self.db.split('/')[-1]
                    graph_dict[each_db]['total_count']=0
                graph_dict[each_db]['topics'][each[0]]=each[1]
                graph_dict[each_db]['total_count']+=each[1]
        '''
        make charts
        '''
        num_rows=math.ceil(len(self.db_list)/2)
        
        fig=plt.figure(figsize=(10,30))
        start_date,end_date=self.get_start_end_dates()
        fig.suptitle(f'Youtube viewing habits for all Libraries\n{start_date} to {end_date}\n')
        
        main_grid=fig.add_gridspec(2,1,height_ratios=[1,3])
        ax1=fig.add_subplot(main_grid[0])
        detail_grid=main_grid[1].subgridspec(num_rows,2,hspace=0.25)
        
        self.color_idx=0
        size_multiplier=50
        total_count=0
        if len(graph_dict.keys())>3:
            angles = np.linspace(0, 2 * np.pi, len(graph_dict.keys()), endpoint=False)          
            angles_ix=0
            for my_db,my_db_dict in graph_dict.items():
                my_color=self.get_color()
                my_count=my_db_dict['total_count']
                total_count+=my_count
                my_x=(center_x + (radius * np.cos(angles[angles_ix])))*1000
                my_y=(center_y + (radius * np.sin(angles[angles_ix])))*1000
                my_size=int(my_count)*size_multiplier
                ax1.scatter(my_x,my_y,s=my_size,label=my_db_dict['name'],color=my_color)
                ax1.annotate(my_count,(my_x,my_y),va='center',ha='center',color='white')
                ax1.annotate(my_db_dict['name'],(my_x,my_y),textcoords='offset points',xytext=(0,math.floor(my_count/2)+5),va='bottom',ha='center',color='black')    
                angles_ix+=1
            my_size=total_count * size_multiplier
            ax1.scatter(center_x, center_y,s=my_size, color='black', label='Center')
            ax1.annotate(total_count,(center_x, center_y),va='center',ha='center',color='white')
            ax1.annotate('Total Views',(center_x,center_y),textcoords='offset points',xytext=(0,math.floor(total_count/2)+5),va='bottom',ha='center',color='black')
        else:
            custom_lines =[]
            legend_labels=[]
            x=0
            total_count=0
            for my_db,my_db_dict in graph_dict.items():
                my_count=my_db_dict['total_count']
                total_count+=my_count
                my_color=self.get_color()
                custom_lines.append(Line2D([0], [0], color=my_color, lw=4))
                legend_labels.append(my_db_dict['name'])
                my_size=int(my_count)*size_multiplier
                ax1.scatter(x,0,s=my_size,label=my_db,color=my_color)
                ax1.annotate(my_count,(x,0),va='center',ha='center',color='white')
                x+=1
            custom_lines.append(Line2D([0], [0], color='black', lw=4))
            legend_labels.append(f'{total_count} Total Views')
            ax1.legend(custom_lines,legend_labels,loc='center left', bbox_to_anchor=(.5,.75))
        ax1.margins(x=0.2,y=0.2)
        ax1.set_xticks([])
        ax1.set_yticks([])
        
        axs_x=-1
        axs_y=0
        for my_db,my_db_dict in graph_dict.items():
            num_markers = len(my_db_dict['topics'].keys())
            angles = np.linspace(0, 2 * np.pi, num_markers, endpoint=False)          
            axs_x+=1
            if axs_x > 1:
                axs_x=0
                axs_y+=1
            angles_ix=0
            axs=fig.add_subplot(detail_grid[axs_y,axs_x])
            axs.set_title(my_db_dict['name'])
            self.color_idx=0
            if len(my_db_dict['topics'].keys()) > 3:
                for topic,my_count in my_db_dict['topics'].items():
                    my_color=self.get_color()
                    my_x=(center_x + (radius * np.cos(angles[angles_ix])))*1000
                    my_y=(center_y + (radius * np.sin(angles[angles_ix])))*1000
                    my_size=int(my_count)*size_multiplier
                    axs.scatter(my_x,my_y,s=my_size,label=topic,color=my_color)
                    axs.annotate(my_count,(my_x,my_y),va='center',ha='center',color='white')
                    axs.annotate(topic,(my_x,my_y),textcoords='offset points',xytext=(0,math.floor(my_count/2)+5),va='bottom',ha='center',color='black')    
                    angles_ix+=1
                my_size=my_db_dict['total_count'] * size_multiplier
                axs.scatter(center_x, center_y,s=my_size, color='black', label='Center')
                axs.annotate(my_db_dict['total_count'],(center_x, center_y),va='center',ha='center',color='white')
            else:
                custom_lines =[]
                legend_labels=[]
                x=0
                total_count=0
                for topic,my_count in my_db_dict['topics'].items():
                    my_color=self.get_color()
                    custom_lines.append(Line2D([0], [0], color=my_color, lw=4))
                    legend_labels.append(topic)
                    total_count+=my_count
                    my_size=int(my_count)*size_multiplier
                    axs.scatter(x,0,s=my_size,label=topic,color=my_color)
                    axs.annotate(my_count,(x,0),va='center',ha='center',color='white')
                    x+=1
                custom_lines.append(Line2D([0], [0], color='black', lw=4))
                legend_labels.append(f'{total_count} Total Views')
                axs.legend(custom_lines,legend_labels,loc='center left', bbox_to_anchor=(.25,.75))
            axs.set_xticks([])
            axs.set_yticks([])
            axs.margins(x=0.2,y=0.25)
            
        fig.tight_layout(pad=2.0)
        
        return self.create_graph()

    def wiki_inventory_by_topic(self):
        plt.clf()
        graphs={}
        stmt='select a.search_text,a.title,count(b.id) '\
           + 'from wikipedia a,youtube b ' \
           + 'where a.id=b.wiki_id '\
           + 'group by 1,2 '\
           + 'order by 1,2;'
        
        view_data=self.get_data(stmt)
        
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
        num_rows=math.ceil(len(graph_dict.keys())/2)
        fig, axs = plt.subplots( num_rows,2, figsize=(15, num_rows * 4),squeeze=False)
        fig.tight_layout(pad=10.0)
        fig.suptitle(f'Youtube Inventory for {self.db.split("/")[-1]}')
        
        axs_x=-1
        axs_y=0
        x=0
        for k,v in graph_dict.items():
            self.color_idx=0
            high=0
            x=0
            axs_x+=1
            if axs_x > 1:
                axs_x=0
                axs_y+=1
            axs[axs_y,axs_x].set_title(k)
            for title,count in v['titles'].items():
                if high<count:high=count
                axs[axs_y,axs_x].bar(title,count,width=0.5,label=title,color=self.get_color())
                axs[axs_y,axs_x].annotate(count,(x,count + 5),va='center',ha='center',fontsize=8)
                x+=1
            axs[axs_y,axs_x].tick_params(axis='x',rotation=30)
            plt.setp(axs[axs_y,axs_x].xaxis.get_majorticklabels(), ha='right')
            axs[axs_y,axs_x].set_ylim(0,high+10)
            axs[axs_y,axs_x].set_xlim(-0.5,len(v['titles'])-0.5)
            #axs[axs_y,axs_x].legend(loc='center left', bbox_to_anchor=(.95,1))
                
        return self.create_graph()

    def views_wordcloud(self):
        plt.clf()
        plt.figure(figsize=(10,10))
        comment_words = ''
        stopwords = set(STOPWORDS)
        stmt='select a.search_text,count(*) ' \
           + 'from wikipedia a,view_counts c '\
           + ' where a.id=c.id ' \
           + ' group by 1 ' \
           + 'UNION ' \
           + 'select b.search_text,count(*) ' \
           + 'from youtube a,wikipedia b,view_counts c '\
           + 'where a.id=c.id '\
           + ' and a.wiki_id=b.id'\
           + ' group by 1 order by 1;'

        view_data=self.get_data(stmt)
        self.logger.debug(f"Word cloud views: {view_data} {len(view_data)}")
        # split the value
        tokens=[]

        for each in view_data:
            self.logger.debug(f"Word cloud view data entry: {each}")
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

        start_date,end_date=self.get_start_end_dates()
        plt.title(f"WordCloud views by Topic for {self.db.split('/')[-1]}\n{start_date} to {end_date}")
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


