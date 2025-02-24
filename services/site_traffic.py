import pusher
from portfolio_base import Portfolio_Base
class Site_traffic(Portfolio_Base):
    """
    Site_traffic
    Handle pusher events stuff
    """
    def __init__(self,*args,**kwargs):
        super(Site_traffic,self).__init__(*args,**kwargs)
        pass
    '''
    'portfolio' channel
    pusher_client = pusher.Pusher(
      app_id='1945852',
      key='eed1abdb9fadef15ad6b',
      secret='1f2dd498073694804fb2',
      cluster='us3',
      ssl=True
    )

    pusher_client.trigger('my-channel', 'my-event', {'message': 'hello world'})
    '''


