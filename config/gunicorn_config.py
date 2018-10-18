bind = '0.0.0.0:9000'
loglevel = 'debug'

workers = 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

def on_starting(server):
    pass

def on_reload(server):
    pass

def on_exit(server):
    pass