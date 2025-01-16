# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 00:21:25 2025

@author: doug_
"""
import os
import sys
import json
import subprocess
import requests


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
    
    def __init__(self,search_string='Miles Davis',max_results=5,cfg='config/.wiki_config.py',*args,**kwargs):
        super(Youtube_reader,self).__init__(*args,**kwargs)
        '''
        I think this is the good one
        '''
        self.__api_key='AIzaSyAQSQZNa3svdV2kg4CIQ5kY_ev95d-ND-Q'
        '''
        these are probably for android stuff
        '''
        self.client_id='609270424962-oegfi73g3jrqasi1ba42c3g35pla6ak5.apps.googleusercontent.com'
        self.client_secret='vEG80N_sYOiTm4UZ1hak_VDS'
        self.url='https://www.googleapis.com/youtube/v3/search'
        self.part='snippet'
        self.q=search_string
        self.max_results=max_results # max 50
        self.url='https://www.googleapis.com/youtube/v3/search'
        self.params = {
                'part': 'snippet',
                'q': self.q,
                'type': 'video',
                'maxResults': self.max_results,
                'order': 'relevance',
                'key':self.__api_key
                }
        '''
        youtube video url
        https://www.youtube.com/watch?v=  +  output['items']['id']['videoId']
        image:
        output["snippet"][""]
        title:
        output["snippet"]["title"]['thumbnails']['default medium high']['url']
        output['snippet']['publishedAt']
        identifier:
        output['etag']
        '''
class Wikipedia_reader(BaseWeb):        
    '''
    Class Wikipedia_reader
    
    sub-class from BaseWeb
    add functionality to read from config and 
    run curl commands to retrieve authentication tokens
    for use with Wikipedia APIs
    '''
    def __init__(self,search_string='Miles Davis',num_pages=3,cfg='cfg/.wiki_credentials',*args,**kwargs):
        super(Wikipedia_reader,self).__init__(*args,**kwargs)
        try:
            with open(cfg,'r') as cf:
                config=cf.read()
        except FileNotFoundError as e:
            print(f"Config file not found, {cfg}.  {e}")
        except Exception as e:
            print(f"Other exception trying to open {cfg}: {e}")
        self.config=json.loads(config) 
        
        self.search_string=search_string
        self.client_credentials=(self.config['wiki_user'],self.config['wiki_pass'])
        self.client=self.config['client_id']
        self.secret=self.config['client_secret']
        self.num_pages=num_pages
        self.MY_APP='https://jackmanu.github.io/portfolio/'
        self.wiki_auth_url="https://meta.wikimedia.org/w/rest.php/oauth2/access_token"
        self.test_api="https://api.wikimedia.org/core/v1/wikipedia/en/page/Earth/bare"
        self.auth_cmd='curl -s -X POST -d "grant_type=client_credentials"' \
            + ' -d "client_id=' + f"{self.client}" + '"' \
            + ' -d "client_secret=' + f"{self.secret}" + '" ' \
            + self.wiki_auth_url 
        self.auth_token=self.get_token(self.auth_cmd)
        '''
        self.bearer_api=api=f'curl -H "Authorization: Bearer {self.auth_token}" ' + self.test_api
        print(f"bearer api:  {self.bearer_api}")
        
        self.bearer_token=self.get_token(self.bearer_api)
        '''
    def call_requests(self,url,headers={},params={}):
        #print('call_requests' + '-' * 40)
        #print(f"    url: {url}")   
        #rint(f"    headers: {headers}")
        #print(f"    params: {params} " )
        try:
            response = requests.get(url, headers=headers, params=params)
        except Exception as e:
            print(f"Exception in call_requests")
            print(f"Response status code: {response.status_code}")
            print(f"call_requests response is a {type(response)}: {json.dumps(response.json(),indent=2)}")

        return response.json()

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
           'User-Agent': 'https://jackmanu.github.io/portfolio/'
        }

        base_url = 'https://api.wikimedia.org/core/v1/wikipedia/'
        endpoint = '/search/page'
        url = base_url + language_code + endpoint
        parameters = {'q': self.search_string, 'limit': self.num_pages}
        output=self.call_requests(url, headers=headers, params=parameters)
        output['search_string']=self.search_string
                    
        return output

if __name__ == '__main__':

    wiki=Wikipedia_reader()
    output=wiki.get_pages('Alan Holdsworth')
    print(f"Output is: \n {json.dumps(output,indent=2)}")
    
    sys.exit(0)
