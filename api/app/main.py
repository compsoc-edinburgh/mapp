from functools import wraps
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext

import secrets
import uuid
import logging
import redis


# Database:
# username:{username} -> {user_id} (STRING)
# users: {user_id_0}, {user_id_1}, ... (SET)
# user:{id} (HASH)
#  username
#  password_hash
#  student_id
#  api_key_hash
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

# Global contexts
redis_client = redis.Redis(decode_responses=True)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
logging.basicConfig(level=logging.INFO)

class UserCreate(BaseModel):
    username: str
    password: str
    student_id: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserEdit(BaseModel):
    username: str | None = None
    password: str | None = None
    student_id: str | None = None

class KeyCreate(BaseModel):
    name: int|None = None
    value: int|None = None

class KeyEdit(BaseModel):
    name: int|None = None
    value: int|None = None

class MachineCreate(BaseModel):
    hostname: str
    is_online: bool
    in_use: bool

class MachineEdit(BaseModel):
    hostname: str | None = None
    is_online: bool | None = None
    in_use: bool | None = None


# some helpful authorization decorators
def get_current_user(request: Request):
    session_user_id = request.session.get("user_id")
    if not session_user_id:
        raise HTTPException(status_code=401, detail="Authorization required.")

    user_data = redis_client.hgetall(f"user:{session_user_id}")
    if not user_data:
        logging.error(f"Valid session for {session_user_id=}, but user does not exist.")
        raise HTTPException(status_code=401, detail="Invalid session, user does not exist.")

    return session_user_id, user_data

def require_roles(*allowed_roles: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if request is None:
                raise RuntimeError("Request parameter is required")
            user_id, user_data = get_current_user(request)
            if user_data.get("account_class") not in allowed_roles:
                raise HTTPException(status_code=403, detail="Not authorized to access resource.")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

admin_required = require_roles("admin")
worker_required = require_roles("admin", "worker")
user_required = require_roles("admin", "user")

# CRUD user accounts
@app.get("/users")
@admin_required
def get_users(request: Request):
    # return list of users
    users = redis_client.smembers("users")
    return {'status': 'success', 'user_ids': list(users)}

@app.post("/users")
def post_users(user: UserCreate):
    # Set user_id, is atomic in redis
    user_id = str(uuid.uuid4()) # https://en.wikipedia.org/wiki/Universally_unique_identifier#Random_UUID_probability_of_duplicates
    success = redis_client.set(f"username:{user.username}", user_id, nx=True)
    if not success:
        raise HTTPException(status_code=400, detail="Username already in use.")
    # Hash the password (argon2 includes salts for us)

    hashed = pwd_context.hash(user.password)
    # Add user to database
    redis_client.hset(f"user:{user_id}",
                      mapping={"username": user.username,
                               "password_hash": hashed,
                               "student_id": user.student_id,
                               "account_class": "user"})
    redis_client.sadd("users", user_id)

    return {"status": "success", "user_id": user_id}

@app.get("/users/{id}")
def get_user(id: str, request: Request):
    # check session has user id
    session_user_id = request.session.get("user_id")
    if not session_user_id:
        raise HTTPException(status_code=401, detail="Authorization required.")
    # check user actually exists and grab data
    session_user_data = redis_client.hgetall(f"user:{session_user_id}")
    if not session_user_data:
        logging.error(f"Valid session for {session_user_id=}, but user does not exist.")
        raise HTTPException(status_code=401, detail="Invalid session, user does not exist.")
    # check if authorized
    if id != session_user_id and session_user_data.get("account_class") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access user record.")
    if id == session_user_id:
        user_data = session_user_data # the logged in user and the requested user are the same, reuse data
    else:
        user_data = redis_client.hgetall(f"user:{id}")
        if not user_data:
            raise HTTPException(status_code=404, detail="Requested user does not exist.")
    # return sanitised version
    safe_user = {k: user_data[k] for k in ["username", "student_id", "account_class"] if k in user_data}
    return {"status": "success", "user": safe_user}

@app.patch("/users/{id}")
def patch_user(id: str, user: UserEdit, request: Request):
    # check session has user id
    session_user_id = request.session.get("user_id")
    if not session_user_id:
        raise HTTPException(status_code=401, detail="Authorization required.")
    # check user actually exists and grab data
    session_user_data = redis_client.hgetall(f"user:{session_user_id}")
    if not session_user_data:
        logging.error(f"Valid session for {session_user_id=}, but user does not exist.")
        raise HTTPException(status_code=401, detail="Invalid session, user does not exist.")
    # check authorization
    if not (session_user_data.get("account_class") == "admin" # if admin, they're allowed to do whatever
            or (session_user_data.get("account_class") == "user" and
                id == session_user_id and not user.student_id)): # users can't change others data, and can't change their own student_id
        raise HTTPException(status_code=403, detail="Unauthorized to make requested change.")
    if user.username:
        # check that username is actually available
        success = redis_client.set(f"username:{user.username}", id, nx=True)
        if not success:
            raise HTTPException(status_code=400, detail="Username already in use.")
        # delete old username -> id record if exists
        if (old_username:=session_user_data.get("username")):
            redis_client.delete(f"username:{old_username}")
        # update user record
        redis_client.hset(f"user:{id}", "username", user.username)
    if user.password:
        hashed = pwd_context.hash(user.password)
        redis_client.hset(f"user:{id}", "password_hash", hashed)
    if user.student_id:
        redis_client.hset(f"user:{id}", "student_id", user.student_id)
    return {"status": "success"}

@app.delete("/users/{id}")
def delete_user(id: str, request: Request):
    # check session has user id
    session_user_id = request.session.get("user_id")
    if not session_user_id:
        raise HTTPException(status_code=401, detail="Authorization required.")
    # check user actually exists and grab data
    session_user_data = redis_client.hgetall(f"user:{session_user_id}")
    if not session_user_data:
        logging.error(f"Valid session for {session_user_id=}, but user does not exist.")
        raise HTTPException(status_code=401, detail="Invalid session, user does not exist.")
    # check if authorized
    if id != session_user_id and session_user_data.get("account_class") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access user record.")
    # check if user actually exists
    user_data = redis_client.hgetall(f"user:{id}")
    if not user_data:
        raise HTTPException(status_code=400, detail="User does not exist")
    # delete user record
    redis_client.delete(f"user:{id}")
    redis_client.srem("users", id)
    # if username didn't exist, throw error after deletion
    username = user_data.get('username')
    if not username:
        raise HTTPException(status_code=400, detail="Currupted user record did not include username.")
    # delete username -> id mapping
    redis_client.delete(f"username:{username}")
    if id == session_user_id:
        request.session["user_id"] = None
    return {"status": "success"}

# Authenticate yourself as a user or worker
@app.post("/auth/login")
def auth(user: UserLogin, request: Request):
    # grab user_id from username
    user_id = redis_client.get(f"username:{user.username}")
    if not user_id:
        logging.info(f"Non-existent user '{user.username}' attempted to authenticate.")
        raise HTTPException(status_code=400, detail="Invalid username or password.")

    # grab user entry from database and verify password
    user_data = redis_client.hgetall(f"user:{user_id}")
    if not user_data:
        logging.error(f"Username {user.username} found in usernames, but {user_id} not found in users.")
        raise HTTPException(status_code=400, detail="Invalid username or password.")
    hashed = user_data.get("password_hash")
    if not hashed:
        logging.error(f"User {user_id} found without password_hash.")
        raise HTTPException(status_code=500, detail=f"Corrupted user record.")
    if not pwd_context.verify(user.password, user_data.get("password_hash")):
        logging.info(f"User '{user.username}' failed login attempt with incorrect password.")
        raise HTTPException(status_code=400, detail="Invalid username or password.")

    # if we've reached this point, the user has successfully logged in, so give them a valid session cookie.
    request.session["user_id"] = user_id
    return {'status': 'success', "user_id": user_id}

# CRUD keys
@app.get("/keys")
@admin_required
def get_keys():
    pass
@app.post("/keys")
@admin_required
def post_keys(key: KeyEdit):
    pass
@app.get("/keys/{id}")
@worker_required
def get_key(id: int):
    pass
@app.patch("/keys/{id}")
@admin_required
def patch_key(id: int, key: KeyCreate):
    pass
@app.delete("/keys/{id}")
@admin_required
def delete_key(id: int):
    pass

# Task queue
@app.post("/tasks/claim")
@worker_required
def claim_task():
    pass
@app.post("/tasks/{id}/drop")
@worker_required
def claim_task(id: int):
    pass

# CRUD machine information
@app.get("/machines")
@user_required
def get_machines():
    pass
@app.post("/machines")
@admin_required
def post_machines(machine: MachineCreate):
    pass
@app.get("/machines/{id}")
@user_required
def get_machine(id: int):
    pass
@app.patch("/machines/{id}")
@worker_required
def patch_machine(id: int, machine: MachineEdit):
    pass
@app.delete("/machines/{id}")
@admin_required
def delete_machine(id: int):
    pass

