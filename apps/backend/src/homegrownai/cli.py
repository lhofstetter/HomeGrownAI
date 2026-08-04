import asyncio

from hypercorn.config import Config
from hypercorn.asyncio import serve
import uvloop

from .main import app

"""
Set Hypercorn configuration:
    - bind to localhost + port number -> reverse proxy using NGINX
    - set number of backlog connections 
    - set maximum enqueued application events
"""

config = Config()
config.bind = ["localhost:4000"]
config.backlog = 1000
config.max_app_queue_size = 100
config.quic_bind = ["localhost:4001"]

uvloop.install()
asyncio.run(serve(app, config)) # ty: ignore
