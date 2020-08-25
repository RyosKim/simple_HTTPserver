from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime


import json, jwt
import sys, os
import time
import mysql.connector as db_connector

SERVER_HOST = 'localhost'
SERVER_PORT = 8008

DB_ENCODE_SECRET = 'guesswhat'
JWT_SECRET = 'jwtpass'
JWT_ALG = 'HS256'
JWT_EXP = 60

db = db_connector.connect(
    host="localhost",
    user="ryos",
    password="1234568"
)
cursor = db.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS interview")
cursor.execute("USE interview")

cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            password VARCHAR(30) NOT NULL,
            joindate DATETIME,
            jwt VARCHAR(255) DEFAULT NULL,
            exp DATETIME DEFAULT NULL
        );
    """)

class ServerHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        print("send header")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_AUTHHEAD(self):
        print ('authen send header')
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        print('received GET request')

    def do_POST(self):
        # Insert user to DB
        if self.path == '/signup':
            length = int(self.headers.get('content-length'))
            message = json.loads(self.rfile.read(length))
            print(message)
            print('received POST request')
            insert_stmt = (
                    """
                    INSERT INTO users (name, password, joindate) 
                    VALUES (%s, ENCODE(%s,%s), %s)
                    """)
            join_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            userData = (message['name'],message['password'], DB_ENCODE_SECRET,join_date)
            try:
                cursor.execute(insert_stmt,userData)
                db.commit()
            except:
                db.rollback()


        elif self.path == '/signin':
            pass


if __name__ == "__main__":
    httpsv = HTTPServer((SERVER_HOST,SERVER_PORT),ServerHandler)
    print(time.asctime(), 'Server started -%s:%s'%(SERVER_HOST, SERVER_PORT))
    httpsv.serve_forever()
    httpsv.server_close()
    print(time.asctime(),'Server Stopped -%s:%s'%(SERVER_HOST, SERVER_PORT))
