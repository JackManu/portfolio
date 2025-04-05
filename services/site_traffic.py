# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 00:21:25 2025

@author: doug_
"""
import os
import sys
import json
from time import strftime
from typing import ClassVar
import pusher
from portfolio_base import Portfolio_Base
from datetime import datetime, timedelta
import math

class Pusher_handler(Portfolio_Base):
    '''
    Class Pusher_handler
    
    Connect to pusher console to publish and retrieve messages
    and other things I haven't read about yet
    '''
    instance_count=0
    __routes={}
    @classmethod
    def update(cls, value):
        cls.__routes = value

    @classmethod
    def get_instance_count(cls):
        # Class method to retrieve the current instance count
        return cls.instance_count

    def __init__(self,*args,**kwargs):
        super(Pusher_handler,self).__init__(*args,**kwargs)
        Pusher_handler.instance_count+=1
        self.app_id=self.config['PUSHER']['connectivity']['app_id']
        self.key=self.config['PUSHER']['connectivity']['key']
        self.secret=self.config['PUSHER']['connectivity']['secret']
        self.cluster=self.config['PUSHER']['connectivity']['cluster']
        if kwargs.get('routes',None):
            self.update(kwargs['routes'])

        if self.config['PUSHER']['connectivity']['ssl']=="True":
            self.ssl=True
        else:
            self.ssl=False
        self.channel='portfolio'

        try:
            self.pusher_client=pusher.Pusher(
            app_id=self.app_id,
            key=self.key,
            secret=self.secret,
            cluster=self.cluster,
            ssl=self.ssl
            )
        except Exception as e:
            print(f"Exception setting up pusher client: {e}")

    def __del__(self):
        self.prune_site_traffic_init()

    def round_to_minutes(self,dt=datetime.now(),min_to_round=10):
        print(f"Site_traffic.py round to minutes input date: {dt} minutes: {min_to_round}")
        my_min=dt.minute
        print(f"Minutes to round: {min_to_round}")
        round_down=math.floor(my_min % min_to_round)
        print(f"Rounded minutes: {round_down}")
        dt.replace(minute=round_down,second=0,microsecond=0)
        print(f"Date after replacing minute: {dt}")
        return dt.replace(minute=math.floor(dt.minute % min_to_round), second=0, microsecond=0)
    
    def send_event(self,event):
        '''
        Currently collecting these by hour
        I think as long as you set display_date to a different increment
        it should work.
        '''

        save_date=self.get_curr_date(format_string="%Y-%m-%d %H:00")
        rt_date=self.get_curr_date(format_string="%Y-%m-%d %H:%M",round_min=5)

        self.logger.debug(f"Sending event: {event} date: {save_date}")
        try:
            output=self.pusher_client.trigger(self.channel,event,{'message-created':rt_date})
        except Exception as e:
            self.db_insert(table_name='errors',type='Pusher',module_name=self.__class__.__name__,error_text=f"Pushing event for {event} {e.args}")
            raise Exception(e)
        '''
        save to datbase so the page can be initialized with current data
        '''
        try:
            self.db_insert(table_name='site_traffic_init',route=event,display_date=save_date)
        except Exception as e:
            self.db_insert(table_name='errors',type='Pusher',module_name=self.__class__.__name__,error_text=f"DB insert to site_traffic_init {event} {e.args}")
            raise Exception(e)
        return output

    def get_init_data(self):
        stmt='select * from (select route,display_date as date,count(*) from site_traffic_init ' \
              + f' group by 1,2 order by route,display_date desc)' \
              + ' as subquery order by date asc;'
        try:
            data=self.exec_statement(stmt)
        except Exception as e:
            self.db_insert(table_name='errors',type='Pusher',module_name=self.__class__.__name__,error_text=f"DB retrieve from site_traffic_init {e.args}")
            raise Exception(e)
        output={each_route:{} for each_route in self.__routes}
        my_dates=[]

        for each in data:
            route=each[0]
            ddate=each[1]
            count=each[2]
            if not output[route].get(ddate,None):
                output[route][ddate]=count
                my_dates.append(ddate)

       
        '''
        print(f"Dates of dict: {sorted(set(my_dates))}")
        print(f"Current output: {json.dumps(output,indent=2)}")
        '''
        '''
        set entries to zeroes for all entries/dates
        '''
        for each_date in sorted(set(my_dates)):
            for k,v in output.items():
                if not output[k].get(each_date,None):
                    output[k][each_date]=0
        
        #print(f"Site traffic returning data: {output}")
       
        return output

    def prune_site_traffic_init(self):
        stmt="delete from site_traffic_init where creation_date < date('now', '-60 days');"

        try:
            deleted_data=self.exec_statement(stmt)
        except Exception as e:
            print(f"Exception pruning site_traffic_init table: {e.args}")

        #self.logger.debug(f"Deleted rows from SITE_TRAFFIC_INIT: {deleted_data}")
        return None

    def test_publish(self):
        
        try:
            output=self.pusher_client.trigger(self.channel, 'my-event', {'message': 'Pushing message from Pusher_handler class in my portfolio site'})
        except Exception as e:
            print(f"Exception is : {e}")
        
        if output:
            return output
        else:
            return 'Nothing returned'
        
if __name__ == '__main__':
     
    pusher=Pusher_handler()
    output=pusher.test_publish()
    print(f"Output is: {output}")
