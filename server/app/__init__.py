import yaml
import falcon
import requests
import json
import logging
from wsgiref import simple_server

from . import resource
from . import middleware
from . import sink
from . import engine

import logging
_logger = logging.getLogger(__name__)



def get_config(filename):
    with open(filename, 'r') as f:
        return yaml.load(f)


config = get_config("config/config.yml")

db_engine = engine.DatabaseEngine(db_path=config['database_path'], datadir=config["data_dir"])

template_engine = engine.TemplateEngine(config["template_dir"])


app = falcon.API(middleware=[
    middleware.DBMiddleware(db_engine=db_engine),
])

run_poster_res = resource.RunPosterResource(db_engine)
run_getter_res = resource.RunGetterResource(db_engine)
run_file_res = resource.RunFileResource(db_engine)

run_leaderboard_res = resource.RunLeaderboardResource(db_engine, template_engine)

sink = sink.Sink()

app.add_sink(sink.get_sink, '/')

app.add_route('/api/run/new', run_poster_res)
app.add_route('/api/run/{run_id}', run_getter_res)
app.add_route('/api/run/{run_id}/files/{file_id}', run_file_res)
app.add_route('/leaderboard/', run_leaderboard_res)
# app.add_route('/runs/', run_getter_res)
# app.add_route('/action/{action_id}/', action_res)
# app.add_route('/subscribe/', action_subs)

# if __name__ == '__main__':
#     httpd = simple_server.make_server('127.0.0.1', 8000, app)
#     httpd.serve_forever()