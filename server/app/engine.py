import re
import logging
import uuid
import falcon
import sqlite3
import os
import time
import jinja2
import logging

_logger = logging.getLogger(__name__)

FILES = {
    "test_pred_labels": 'application/csv',
    "test_pred_probs": 'application/csv '
}
COLUMNS = [
    "timestamp",
    "run_id",
    "loss",
    "acc",
    "val_loss",
    "val_acc",
]

ORDERS = ["DESC", "ASC"]

class Engine(object):
    def __init__(self):
        pass

    def get_new_uuid(self):
        return str(uuid.uuid4())

class TemplateEngine(Engine):
    def __init__(self, template_path):
        self.loader = jinja2.FileSystemLoader(searchpath=template_path)
        self.env = jinja2.Environment(loader=self.loader)

    def render(self, template, **data):
        return self.env.get_template(template).render(**data)

class DatabaseEngine(Engine):
    def __init__(self, db_path, datadir):
        os.makedirs(datadir, exist_ok=True)

        self.datadir = datadir
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
        self.conn.execute('''CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY UNIQUE, 
            timestamp INT,
            loss REAL NOT NULL, 
            acc REAL NOT NULL, 
            val_loss REAL NOT NULL, 
            val_acc REAL NOT NULL
        )''')
        self.conn.commit()

    def add_run(self, cursor, run_data):
        _logger.debug("Adding run {}".format(run_data))
        try:
                
            cursor.execute("INSERT INTO runs VALUES (?,?,?,?,?,?)",
                [
                    run_data["run_id"],
                    int(time.time()),
                    run_data["loss"],
                    run_data["acc"],
                    run_data["val_loss"],
                    run_data["val_acc"],
                ]
            )
            self.conn.commit()
            success = True
    
        except sqlite3.Error as er:
            _logger.error("Database error: {}".format(er))
            success = False
        
        if success:
            for file_id in FILES:
                with open(os.path.join(self.datadir, "{}-{}.csv".format(run_data["run_id"], file_id)), "w") as f:
                    f.write(run_data[file_id])

        return run_data["run_id"] if success else None

    def get_run(self, cursor, run_id):
        _logger.debug("Getting run {}".format(run_id))

        cursor.execute("SELECT * FROM runs WHERE run_id = '{}'".format(run_id))
        result = cursor.fetchall()

        return result

    def get_file(self, cursor, run_id, file_id):
        filename = "{}-{}.csv".format(run_id, file_id)
        file_path = os.path.join(self.datadir, filename)
        if file_id in FILES and os.path.isfile(file_path):
            with open(file_path, "r") as f:
                file_data = f.read()
                return (file_data, FILES[file_id]), filename
        else:
            return None, None
    
    def get_runs(self, cursor, order_by, order, start, count):

        if order_by not in COLUMNS:
            _logger.error("Invalid order_by")
            return []
        if order not in ORDERS:
            _logger.error("Invalid order")
            return []
        else:
            try:
                db_string = "SELECT * FROM runs ORDER BY {} {}".format(order_by, order)
                _logger.debug(db_string)
                cursor.execute(db_string)
                result = cursor.fetchall()
                return result
            except sqlite3.Error as er:
                _logger.error("Database error: {}".format(er))
                return []
        
        
