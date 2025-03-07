class Globals:
    """
    Hold global variable values
    for now it is needed for base_uri
    """
    base_uri='not_defined'
    def __init__(self,base_uri='passed_in',*args,**kwargs):
        print("Inside of Globals init uri passed in: {base_uri}")
        Globals.base_uri=base_uri
        print("Inside of Globals class variable: {Globals.base_uri}")



