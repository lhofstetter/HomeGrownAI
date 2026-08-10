from uvicorn import Config, Server
import uvloop

from .main import app

"""
Set Hypercorn configuration:
    - bind to localhost + port number -> reverse proxy using NGINX
    - set number of backlog connections 
    - set maximum enqueued application events
"""

uvloop.install()

config = Config(
    app=app,
    host="127.0.0.1",
    port=8000,
    loop="uvloop",
    http="httptools",
    workers=1,
    lifespan="on",
    # server_header=False,
    access_log=False,
    # proxy_headers=True,
    # forwarded_allow_ips="127.0.0.1",
    backlog=1000,
)

server = Server(config)
server.run()
