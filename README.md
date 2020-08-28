# simple_HTTPserver
## Python simple HTTPserver for authentication

### Pre-requirement:
   - This server require the following modules to run: jwt, json, mysql-python
   - This server also require a running mysql server, you can modify user credentials and server port in server.py file

### This server support the following API:
   1. SIGNUP: URI: "/signup", method POST
        - Required body key: login_id, password, email
        - Server will create a user record in db without jwt token

   2. SIGNIN: URI: "/signin", method POST
        - Required body key: loging_string, password
        - After verify user credentials, server return token to client and save token to db
        - Token payload structure: {"login_id": user_login_id, "exp": token exp timestamp} 
        - Token will be update to db everytime user send a SIGNIN request

   3. LOGOUT: URI: "/logout", method GET
        - Required logged in.
        - Token must be included in header['Authorization']
        - After logout, stored token in db will be remove 

   4. Default request to URI : "/" method GET will check logged in status of user
        - Token must be included in header['Authorization']
        - Token will be expired at token.payload['exp'], if current timestamp is larger or equal to exp. server return error message to ask user to login again without querying the db.
        - If token is not expired server query db to verify that token still exists which means user hasn't logged out yet.

### Database:
   - This HTTPserver use a MySQL db
   - DB include a table named "users" store user's credential, email and token of current login section.
