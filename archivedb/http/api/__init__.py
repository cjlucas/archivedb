#import archivedb.config as config
import os

def _find_apis():
    apis = {}
    for f in os.listdir(os.path.dirname(__file__)):
        if f.endswith(".py") and f != "__init__.py":
            api_name = os.path.splitext(f)[0].lower()
            apis[api_name] = "archivedb.http.api." + api_name

    return(apis)
