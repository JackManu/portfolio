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

class BaseWeb():
    '''
    Class BaseWeb
    
    simple base class to allow request calls for my portfolio to demonstrate
    inheritance.
    '''
    def __init__(self):
    
        def call_requests(self,url,headers={},params={}):
            #print('call_requests' + '-' * 40)
            #print(f"    url: {url}")   
            #print(f"    headers: {headers}")
            #print(f"    params: {params} " )
            try:
                response = requests.get(url, headers=headers, params=parameters)
            except Exception as e:
                print(f"Exception in call_requests")
                print(f"Response status code: {response.status_code}")
                print(f"call_requests response is a {type(response)}: {json.dumps(response.json(),indent=2)}")
        
            return response.json()
    
class Youtube_reader():
    '''
    Class Youtube_reader
    
    sub-class from BaseWeb to do request calls for youtube videos
    '''
    def __init__(self):
        pass
        
class Wikipedia_reader():
    '''
    Class Wikipedia_reader
    
    sub-class from BaseWeb
    add functionality to read from config and retrieve authentication tokens
    for use with Wikipedia APIs
    '''
    def __init__(self,search_string='Miles Davis',cfg='cfg/.wiki_credentials'):
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
        parameters = {'q': self.search_string, 'limit': number_of_results}
        output=self.call_requests(url, headers=headers, params=parameters)
        return_list=[]
        count=0
        
        for page in output['pages']:
            temp_dict={}
            temp_dict['artist']=self.search_string
            temp_dict['title']=page.get('title','no_title')
            temp_dict['thumbnail']=page.get('thumbnail',"Nothing found")
            temp_dict['excerpt']=page.get('excerpt','no_excerpt')
            return_list.append(temp_dict)
            
        
        return return_list

if __name__ == '__main__':

    wiki=Wikipedia_reader()
    output=wiki.get_pages('Alan Holdsworth')
    print(f"Output is: \n {json.dumps(output,indent=2)}")
    
    sys.exit(0)


