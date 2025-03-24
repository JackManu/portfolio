# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 00:21:25 2025

@author: doug_
"""
import os
import sys
import json
from typing import ClassVar
import pusher
from portfolio_base import Portfolio_Base
    
class Pusher_handler(Portfolio_Base):
    '''
    Class Pusher_handler
    
    Connect to pusher console to publish and retrieve messages
    and other things I haven't read about yet
    '''
    __routes={}
    @classmethod
    def update(cls, value):
        cls.__routes = value

    def __init__(self,*args,**kwargs):
        super(Pusher_handler,self).__init__(*args,**kwargs)
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

        '''
        We don't need to subscribe to this,  we're just publishing to it
        try:
            self.pusher_client.subscribe(self.channel)
        except Exception as e:
            print(f"Exception subscribing to channel: {e}")
        '''
    def __del__(self):
        self.prune_site_traffic_init()

    def send_event(self,event):
        display_date=f'{self.get_curr_date().split(" ")[1][:5]}:00'
        try:
            output=self.pusher_client.trigger(self.channel,event,{'message-created':display_date})
        except Exception as e:
            self.db_insert(table_name='errors',type='Pusher',module_name=self.__class__.__name__,error_text=f"Pushing event for {event} {e.args}")
            raise Exception(e)
        '''
        save to datbase so the page can be initialized with current data
        '''
        try:
            self.db_insert(table_name='site_traffic_init',route=event,display_date=display_date)
        except Exception as e:
            self.db_insert(table_name='errors',type='Pusher',module_name=self.__class__.__name__,error_text=f"DB insert to site_traffic_init {event} {e.args}")
            raise Exception(e)
        return output

    def prune_site_traffic_init(self):
        stmt="delete from site_traffic_init where creation_date < date('now', '-14 days');"

        try:
            deleted_data=self.exec_statement(stmt)
        except Exception as e:
            print(f"Exception pruning site_traffic_init table: {e.args}")

        #self.logger.debug(f"Deleted rows from SITE_TRAFFIC_INIT: {deleted_data}")
        return None

    def get_init_data(self):
        output={}
        '''
        try doing this by hour instead of minute
        '''
        #stmt='select route,substring(display_date,1,2),count(*) from site_traffic_init ' \
        stmt='select route,display_date,count(*) from site_traffic_init ' \
            + ' group by 1,2 order by 1,creation_date desc;'
        try:
            data=self.exec_statement(stmt)
        except Exception as e:
            self.db_insert(table_name='errors',type='Pusher',module_name=self.__class__.__name__,error_text=f"DB retrieve from site_traffic_init {e.args}")
            raise Exception(e)
        for each in data:
            route=each[0]
            ddate=each[1]
            count=each[2]
            if not output.get(route,None):
                output[route]=[]
                output[route].append([ddate,count])
            else:
                #  only take the 5 latest entries.  reverse is below
                if len(output[route]) < 10:
                    output[route].append([ddate,count])

        # reverse the lists
        new_output={}
        for k,v in output.items():
            if not new_output.get(k,None):
                new_output[k]=[]
                new_output[k]=v[::-1]
    
        return new_output

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
