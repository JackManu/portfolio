
import sys
import jinja2
import os
import json
import datetime
from pathlib import Path
from flask import url_for, render_template
class HelperException(Exception):
    pass
class Helper:
    def __init__(self):
        self.base_uri=Path(__file__).parent.parent / 'templates'
        self.pvars={'base_uri':self.base_uri}
    def render_html(self,file='index.html'):
       try:
           
           my_jinja=jinja2.FileSystemLoader(searchpath=self.base_uri)
           my_jinja_env=jinja2.Environment(loader=my_jinja)
           template=my_jinja_env.get_template(file)
           output=template.render(self.pvars)
           #output=render_template(file,data=self.pvars)
       except Exception as e:
           raise HelperException(e)
       else:
           return output