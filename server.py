from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta, timezone

import json, jwt
import sys, os
import time
import mysql.connector as db_connector

SERVER_HOST = 'localhost'
SERVER_PORT = 8008

JWT_SECRET = 'jwtpass'
JWT_ALG = 'HS256'

db = db_connector.connect(
    host="localhost",
    user="ryos",
    password="1234568"
)
cursor = db.cursor()
cursor.execute("USE interview")

# Insert new user to DB: login_id, password, email and joined_date
def insert_user(login_id,password,email):
    insert_stmt = (
            """
            INSERT INTO users (login_id, password, email, joindate) 
            VALUES (%s, SHA1(%s), %s, %s)
            """)
    join_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    userData = (
            login_id,
            password, 
            email,
            join_date)            
    try:
        cursor.execute(insert_stmt,userData)
        db.commit()
        print('User added')
    except:
        db.rollback()
        print('Failed to add user')

# Update user record to manage login section: store jwt at first login and expand exp when relogin
def update_db(login_id,token):
    query_stmt = (
            """
            UPDATE users
            SET jwt = %s
            WHERE login_id = %s
            """)
    query_param = (token,login_id)
    try:
        cursor.execute(query_stmt,query_param)
        db.commit()
        print('DB updated successfully!')
        return 1
    except:
        db.rollback()
        print('Failed to update DB')
        return 0

# Find user by password: Used for loggin section
def query_user_by_password(login_string,password):
    query_stmt = (
            """
            SELECT login_id, jwt
            FROM users
            WHERE (SHA1(%s) = password) 
            AND (login_id = %s OR email = %s)
            """)
    query_param = (password,login_string,login_string)
    cursor.execute(query_stmt,query_param)
    return cursor.fetchall()

# Find user by token: Used to check authorization
def query_user_by_token(login_id,token):
    query_stmt = (
            """
            SELECT * 
            FROM users
            WHERE login_id = %s
                AND jwt = %s
            """)
    query_param = (login_id,token)
    cursor.execute(query_stmt,query_param)
    return cursor.fetchall()

# Check token exp: Raise error when token exp < current timestamp or token deleted from db
def verify_token(token):
    payload = jwt.decode(token,JWT_SECRET)
    if payload['exp'] < datetime.timestamp(datetime.now(timezone.utc)): 
        print('Expired')
        return 0
    elif len(query_user_by_token(payload['login_id'],token)) == 0: 
        print('User not found')
        return 0
    return 1

# Delete Token after logged out: Deleted token on DB
def delete_token(login_id):
    return update_db(login_id,None)

class ServerHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        print('received GET request')
        
        if self.headers.get('Authorization') == None or self.headers.get('Authorization') == 'Null':
            self.send_error(401,"Login required!")
        else:
            token = self.headers.get('Authorization')
            if self.path == '/':
                if verify_token(token) == 1:
                    self.do_HEAD()
                    self.wfile.write(bytes("All good, Have a nice day","utf-8"))
                else:
                    self.send_error(401,"Section time out or user logged out, please try login again")
            elif self.path == '/logout':
                payload = jwt.decode(token,JWT_SECRET)
                if delete_token(payload['login_id']) == 1:
                    self.do_HEAD()
                    self.wfile.write(bytes("Logged out!", "utf-8"))
                else:
                    self.send_error(500,"Failed to delete token, please try again!")
            else:
                self.send_error(421, "Unknown URI")

    def do_POST(self):
        length = int(self.headers.get('Content-length'))
        message = json.loads(self.rfile.read(length))

        # User sign up: Save user credentials to DB
        if self.path == '/signup':
            print('Received SIGNUP request')
            required_key = ['login_id','password','email']
            try:
                if all(message[key] != '' for key in required_key):
                    insert_user(message['login_id'],message['password'],message['email'])
                    self.do_HEAD()
                    self.wfile.write(bytes("Signed up successfully, please login","utf-8"))
                else:
                    self.send_error(456,'Sign up Key error1: Missing required field or field empty')
            except:
                self.send_error(456,'Sign up Key error2: Missing required field or field empty')

        # User login, return new jwt if successfully authenticated
        elif self.path == '/signin':
            print('Received SIGNIN request')
            try:
                if message ['login_string'] != "" and message['password'] != "":
                    result = query_user_by_password(message['login_string'],message['password'])
                    if len(result) > 0:
                        credent = result[0]
                        exp = datetime.now(timezone.utc)+timedelta(days=1)
                        token = jwt.encode({
                                'login_id':credent[0],
                                'exp':exp},
                                key=JWT_SECRET,algorithm=JWT_ALG).decode("utf-8")
                        update_db(credent[0],token)
                        self.do_HEAD()
                        self.wfile.write(bytes(token,"utf-8"))
                        print('Logged in successfully')                        
                    else:
                        self.send_error(404,'Credential not found or wrong user password')
                else:
                    self.send_error(456,'Sign in Key error1: Missing required field or field empty')
            except:
                self.send_error(456,'Sign in Key error2: Missing required field or field empty')
        else:
            self.send_error(421, 'Unknown URI')

if __name__ == "__main__":
    httpsv = HTTPServer((SERVER_HOST,SERVER_PORT),ServerHandler)
    print(time.asctime(), 'Server started -%s:%s'%(SERVER_HOST, SERVER_PORT))
    httpsv.serve_forever()
    httpsv.server_close()
    print(time.asctime(),'Server Stopped -%s:%s'%(SERVER_HOST, SERVER_PORT))
    
