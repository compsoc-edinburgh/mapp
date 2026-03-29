from fastapi import FastAPI, HTTPException
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

import secrets

# Database:
# username:{username} -> {user_id} (STRING)
# user:{id} (HASH)
#  username
#  password_hash
#  password_salt
#  student_id
#  api_key_hash
#  api_key_salt
#  account_class: (one of admin, user, or worker)
# machine:{hostname} (HASH)
#  ip: "1.2.3.4"
#  status: "active"
#  last_seen: 1710000000
# machines  (SET)
#  "host123"
#  "host456"

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_hex(0x20) # invalidates sessions on restart, this is ok
)

class User(BaseModel):
    id: int|None
    username: str|None
    password: str|None
    student_id: str|None
    account_class: str|None
    api_key: str|None

class Key(BaseModel):
    id: int|None
    name: int|None
    value: int|None

class Machine(BaseModel):
    hostname: str
    is_online: bool
    in_use: bool

# CRUD user accounts
@app.get("/users")
def get_users():
    pass
@app.post("/users")
def post_users(user: User):
    pass
@app.get("/users/{id}")
def get_user(id: int):
    pass
@app.patch("/users/{id}")
def patch_user(id: int, user: User):
    pass
@app.delete("/users/{id}")
def delete_user(id: int):
    pass

# Authenticate yourself as a user or worker
@app.post("/auth/login")
def auth(user: User):
    pass

# CRUD keys
@app.get("/keys")
def get_keys():
    pass
@app.post("/keys")
def post_keys(user: User):
    pass
@app.get("/keys/{id}")
def get_key(id: int):
    pass
@app.patch("/keys/{id}")
def patch_key(id: int, user: User):
    pass
@app.delete("/keys/{id}")
def delete_key(id: int):
    pass

# Task queue
@app.post("/tasks/claim")
def claim_task():
    pass
@app.post("/tasks/{id}/drop")
def claim_task(id: int):
    pass

# CRUD machine information
@app.get("/machines")
def get_machines():
    pass
@app.post("/machines")
def post_machines(user: User):
    pass
@app.get("/machines/{id}")
def get_machine(id: int):
    pass
@app.patch("/machines/{id}")
def patch_machine(id: int, user: User):
    pass
@app.delete("/machines/{id}")
def delete_machine(id: int):
    pass

