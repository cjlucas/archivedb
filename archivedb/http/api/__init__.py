import archivedb.config as config
import os
import sys

def _find_apis():
    apis = {}
    for f in os.listdir(os.path.dirname(__file__)):
        if f.endswith(".py") and f != "__init__.py":
            api_name = os.path.splitext(f)[0]
            __import__("archivedb.http.api." + api_name)
            apis[api_name.lower()] = getattr(sys.modules["archivedb.http.api"], api_name)

    return(apis)


_api_dict = _find_apis()
