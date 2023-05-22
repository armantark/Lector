from urllib.parse import urlparse
import os
from psycopg2 import pool


class BotDatabase:
    def __init__(self, minconn, maxconn, url):
        result = urlparse(url)
        self.db_pool = pool.SimpleConnectionPool(
            minconn,
            maxconn,
            dbname=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )

    def get_conn(self):
        return self.db_pool.getconn()

    def put_conn(self, conn):
        return self.db_pool.putconn(conn)

    # Your other methods...


# You can read the DATABASE_URL from your environment variables
database_url = os.getenv("DATABASE_URL")

# Create an instance of your database with a pool of 1 to 5 connections
db = BotDatabase(1, 5, database_url)
