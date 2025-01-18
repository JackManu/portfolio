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
from db_helper import DB_helper


class BaseWeb(object):
    '''
    Class BaseWeb
    
    simple base class to allow requests calls for my portfolio to demonstrate
    inheritance.
    '''
    def __init__( self,*args, **kwargs):
        pass

    def call_requests(self,url,headers={},params={}):
        #print('call_requests' + '-' * 40)
        #print(f"    url: {url}")   
        #print(f"    headers: {headers}")
        #print(f"    params: {params} " )
        try:
            response = requests.get(url, headers=headers, params=params)
        except Exception as e:
            print(f"Exception in call_requests")
            print(f"Response status code: {response.status_code}")
            print(f"call_requests response is a {type(response)}: {json.dumps(response.json(),indent=2)}")

        return response.json()
    
class Youtube_reader(BaseWeb):
    '''
    Class Youtube_reader
    
    sub-class from BaseWeb to do request calls for youtube videos
    '''
    
    def __init__(self,search_text='Miles Davis',wiki_id=None,max_results=50,cfg='cfg/.config',*args,**kwargs):
        super(Youtube_reader,self).__init__(*args,**kwargs)
        '''
        put this config stuff in the base class so people won't think you're an idiot
        '''
        try:
            with open(cfg,'r') as cf:
                config=cf.read()
            self.config=json.loads(config)
        except FileNotFoundError as e:
            print(f"Config file not found, {cfg}.  {e}")
        except Exception as e:
            print(f"Other exception trying to open {cfg}: {e}")
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
  
    def load_db(self):
        mydb=DB_helper()
        output=[]
        try:
            output=self.call_requests(self.config['youtube_search'],params=self.params)
        except Exception as e:
            print(f"Got exception calling youtube.  {e}")
    
        #print(f"youtube get_pages Output is: \n {json.dumps(output,indent=2)}")
    
        pages=[]
        for each in output['items']:
            temp_dict={}
            temp_dict['id']=each['etag']
            temp_dict['wiki_id']=self.wiki_id
            temp_dict['search_text']=self.search_text
            temp_dict['video_id']=each['id']['videoId']
            temp_dict['url']=self.config['youtube_url'] + temp_dict['video_id']
            temp_dict['description']=each['snippet']['description']
            temp_dict['title']=each['snippet']['title']
            temp_dict['thumbnail']=each['snippet']['thumbnails']['default']
            #print(f"Inside youtube load pages temp dict: {json.dumps(temp_dict,indent=2)}")
            pages.append(temp_dict)
            mydb.db_insert('Youtube',temp_dict['id'],temp_dict['wiki_id'],temp_dict['title'],temp_dict['url'],temp_dict['description'],temp_dict['thumbnail'],temp_dict['video_id'],temp_dict['wiki_id'])
    
        return pages
class Wikipedia_reader(BaseWeb):        
    '''
    Class Wikipedia_reader
    
    sub-class from BaseWeb
    add functionality to read from config and 
    run curl commands to retrieve authentication tokens
    for use with Wikipedia APIs
    '''
    def __init__(self,search_text='Miles Davis',num_pages=3,cfg='cfg/.config',*args,**kwargs):
        super(Wikipedia_reader,self).__init__(*args,**kwargs)
        try:
            with open(cfg,'r') as cf:
                config=cf.read()
            self.config=json.loads(config)
        except FileNotFoundError as e:
            print(f"Config file not found, {cfg}.  {e}")
        except Exception as e:
            print(f"Other exception trying to open {cfg}: {e}")
        
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
            print(f"Exception running curl: {e}")
            return None
        if error:
            print(f"Error getting authentication token.\n  {error}")
            sys.exit(0)
        #print(f"Output popen: {output}")
        
        jout=json.loads(output.decode('utf-8'))
        token=jout['access_token']
        #print(f"OUTPUT:  {type(jout)} {token}")
        
        return token
    def get_pages(self):
        language_code = 'en'
        number_of_results = 15
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
        for each in output['pages']:
            each['url']=self.config['wiki_page_url']+str(each['id'])
            each['search_text']=self.search_text
                    
        return output

if __name__ == '__main__':

    wiki=Wikipedia_reader()
    output=wiki.get_pages('Alan Holdsworth')
    print(f"Output is: \n {json.dumps(output,indent=2)}")
    
    sys.exit(0)
