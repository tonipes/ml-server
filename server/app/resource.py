import logging
import urllib
import re
import threading
import json
import falcon
import logging
import datetime

_logger = logging.getLogger(__name__)

from . import engine

class Resource(object):
    pass

class RunLeaderboardResource(Resource):
    def __init__(self, db_engine, template_engine):
        self.db_engine = db_engine
        self.template_engine = template_engine

    def on_get(self, req, resp):
        order_by = req.get_param("order_by", required=False)
        order = req.get_param("order", required=False)
        start = req.get_param_as_int("start", required=False, min=0, max=None)
        count = req.get_param_as_int("count", required=False, min=1, max=1000)
        
        if not order_by: order_by = "val_acc"
        if not start: start = 0
        if not count: count = 100
        if not order: order = "ASC"

        runs = self.db_engine.get_runs(self.cursor, order_by, order, start, count)
        
        for run in runs:
            run["timestamp"] = datetime.datetime.fromtimestamp(run["timestamp"])
            for f in engine.FILES:
                run[f] = "{}-{}".format(run["run_id"], f)

        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        resp.body = self.template_engine.render("leaderboard.html", 
            order_by=order_by, 
            order=order,
            start=start, 
            count=count, 
            runs=runs,
            columns=engine.COLUMNS,
            orders=engine.ORDERS
            )

class RunFileResource(Resource):
    def __init__(self, db_engine):
        self.db_engine = db_engine

    def on_get(self, req, resp, run_id, file_id):
        run_file_data, filename = self.db_engine.get_file(self.cursor, run_id, file_id)

        if run_file_data:
            resp.body, resp.content_type = run_file_data
            resp.append_header("content-disposition", "attachment; filename=\"{}\"".format(filename))
            resp.status = falcon.HTTP_200
        else:
            resp.status = falcon.HTTP_404

class RunPosterResource(Resource):
    def __init__(self, db_engine):
        self.db_engine = db_engine

    def on_post(self, req, resp):
        run_id = self.db_engine.add_run(self.cursor, req.media)

        if run_id:
            resp.media = {"run_id": run_id}
            resp.status = falcon.HTTP_200
        else:
            resp.status = falcon.HTTP_409

class RunGetterResource(Resource):
    def __init__(self, db_engine):
        self.db_engine = db_engine

    def on_get(self, req, resp, run_id):
        run_data = self.db_engine.get_run(self.cursor, run_id)

        if run_data:
            resp.media = run_data
            resp.status = falcon.HTTP_200
        else:
            resp.status = falcon.HTTP_404

