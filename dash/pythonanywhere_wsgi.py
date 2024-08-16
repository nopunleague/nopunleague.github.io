import sys

project_home = u'/home/majedo/npl/dash'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

from dashing_demo_app import app
application = app.server
