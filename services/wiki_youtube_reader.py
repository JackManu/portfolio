# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 00:21:25 2025

@author: Doug McIntosh
"""
import os
import sys
import json
import subprocess
import requests
from portfolio_base import Portfolio_Base


class BaseWeb(Portfolio_Base):
    '''
    Class BaseWeb
    
    allow requests calls for my portfolio 
    '''
    def __init__( self,*args, **kwargs):
        super(BaseWeb,self).__init__(*args,**kwargs)

    def call_requests(self,url,headers={},params={}):
        '''
        we hopefully won't need this
        self.logger.debug('call_requests' + '-' * 40)
        self.logger.debug(f"    url: {url}")   
        self.logger.debug(f"    headers: {headers}")
        self.logger.debug(f"    params: {params} " )
        '''
        try:
            response = requests.get(url, headers=headers, params=params)
        except Exception as e:
            self.db_insert(table_name='errors',type='Python requests',module_name=self.__class__.__name__,error_text=f"status code: {response.status_code} exception: {e}")
            self.logger.error(f"Exception in call_requests  {self.__class__.__name__}")
            self.logger.error(f"Response status code: {response.status_code}")
            self.logger.error(f"call_requests response is a {type(response)}: {json.dumps(response.json(),indent=2)}")
            raise Exception(e,self.__class__.__name__)
            
        if response.status_code != 200:
            self.db_insert(table_name='errors',type='Python requests',module_name=self.__class__.__name__,error_text=f"status code: {response.status_code} for api: {url} ")
            return {f"{response.status_code}":f"error calling {url} in {self.__class__.__name__}"}
        else:
            #self.logger.debug(f"Response: {json.dumps(response.json(),indent=2)}")
            return response.json()
    
class Youtube_reader(BaseWeb):
    '''
    Class Youtube_reader
    
    sub-class from BaseWeb to do request calls for youtube videos
    '''
    
    def __init__(self,search_text='Miles Davis',wiki_id=None,max_results=20,*args,**kwargs):
        super(Youtube_reader,self).__init__(*args,**kwargs)
        self.part='snippet'
        self.wiki_id=wiki_id
        self.search_text=search_text
        self.max_results=max_results # max 50
        self.params = {
                'part': 'snippet',
                'q': self.search_text,
                'type': 'video',
                'maxResults': self.max_results,
                'order': 'relevance',
                'key':self.config['google_api_key']
                }

    def handle_db(self,insert=True,):
        output=[]
        self.logger.debug(f"Youtube_reader handle_db insert: {insert}")
        sel_stmt=f"select id from youtube where wiki_id='{self.wiki_id}';"
        current_entries=[each[0] for each in self.exec_statement(sel_stmt)]
        self.logger.debug(f"Current youtube entries: {current_entries}")
        try:
            output=self.call_requests(self.config['youtube_search'],params=self.params)
        except Exception as e:
            self.logger.error(f"Exception in {self.__class__.__name__}")
            raise Exception(e,self.__class__.__name__)

        #self.logger.debug(f"youtube get_pages Output is: \n {json.dumps(output,indent=2)}")
    
        pages=[]
        if output.get('items',None):
            for each in output['items']:
                temp_dict={}
                self.logger.debug(f"ETAG: {each['etag']}")
                if each['etag'] not in current_entries:
                    temp_dict['id']=each['etag']
                    temp_dict['wiki_id']=self.wiki_id
                    temp_dict['search_text']=self.search_text
                    temp_dict['video_id']=each['id'].get('videoId','Not_Found')
                    temp_dict['url']=self.config['youtube_url'] + temp_dict['video_id']
                    temp_dict['description']=each['snippet']['description']
                    temp_dict['title']=each['snippet']['title']
                    temp_dict['thumbnail']=each['snippet']['thumbnails']['default']
                    pages.append(temp_dict)
                    if insert:
                        self.db_insert(table_name='Youtube',my_id=temp_dict['id'],wiki_id=temp_dict['wiki_id'],title=temp_dict['title'],url=temp_dict['url'],description=temp_dict['description'],thumbnail=temp_dict['thumbnail'],video_id=temp_dict['video_id'])
    
        return pages

class Wikipedia_reader(BaseWeb):        
    '''
    Class Wikipedia_reader
    
    sub-class from BaseWeb
    add functionality to read from config and 
    run curl commands to retrieve authentication tokens
    for use with Wikipedia APIs
    '''
    def __init__(self,search_text=None,num_pages=None,*args,**kwargs):
        super(Wikipedia_reader,self).__init__(*args,**kwargs)
        
        if search_text:
            self.search_text=search_text
            self.client_credentials=(self.config['wiki_user'],self.config['wiki_pass'])
            self.client=self.config['client_id']
            self.secret=self.config['client_secret']
            self.num_pages=num_pages
            self.MY_APP=self.config['MY_APP']
            self.wiki_auth_url=self.config['wiki_auth_url']
            #self.test_api="https://api.wikimedia.org/core/v1/wikipedia/en/page/Earth/bare"
            self.auth_cmd='curl -s -X POST -d "grant_type=client_credentials"' \
                + ' -d "client_id=' + f"{self.client}" + '"' \
                + ' -d "client_secret=' + f"{self.secret}" + '" ' \
                + self.wiki_auth_url 
            self.auth_token=self.get_token(self.auth_cmd)
   
    def get_token(self,api): 
        '''

        Parameters
        ----------
        api : wiki authentication api
            DESCRIPTION.

        Returns
        -------
        authorization token

        '''
    
        #print('call_curl' + '-' * 40)
        #print(f"cmd : {api}")        
        try:
            resp=subprocess.Popen(api,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)                           
            output,error=resp.communicate()
        except Exception as e:
            self.db_insert(table_name='errors',type='curl-subprocess',module_name=self.__class__.__name__,error_text=f"Api: {api} subprocess error: {error} exception: {e}")
            self.logger.error(f"Exception running curl: {e}")
            raise Exception(e,self.__class__.__name__)
        #self.logger.debug(f"Output popen: {output}")
        
        jout=json.loads(output.decode('utf-8'))
        if not jout.get('access_token',None):
            token=''
            self.db_insert(table_name='errors',type='curl-subprocess',module_name=self.__class__.__name__,error_text=f"Api: {api} subprocess did not return a token")
        else:
            token=jout['access_token']
        
        return token

    def get_pages(self):
        language_code = 'en'
        headers = {
           'Authorization': f'Bearer {self.auth_token}',
           'User-Agent': self.config['MY_APP']
        }

        base_url = self.config['wiki_base_url']
        endpoint = '/search/page'
        url = base_url + language_code + endpoint
        parameters = {'q': self.search_text, 'limit': self.num_pages}
        output=self.call_requests(url, headers=headers, params=parameters)
        output['search_text']=self.search_text
        sel_stmt=f"select distinct id from wikipedia where search_text like '{self.search_text}%';"
        current_entries=[each[0] for each in self.exec_statement(sel_stmt)]
        filtered_pages=[each for each in output['pages'] if each['id'] not in current_entries]
        for each in filtered_pages:
            each['url']=self.config['wiki_page_url']+str(each['id'])
            each['search_text']=self.search_text
        output['pages']=filtered_pages
                    
        return output

if __name__ == '__main__':

    wiki=Wikipedia_reader()
    output=wiki.get_pages('Alan Holdsworth')
    print(f"Output is: \n {json.dumps(output,indent=2)}")
    
    sys.exit(0)
