from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from app.deps import admin_required, get_redis, get_pwd_context

import secrets
import uuid
import logging
import redis
import os

router = APIRouter()

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


# CRUD user accounts
@router.get("/")
def get_users(request: Request, user=Depends(admin_required), redis_client=Depends(get_redis)):
    # return list of users
    users = redis_client.smembers("users")
    return {'status': 'success', 'user_ids': list(users)}

@router.post("/")
def post_users(user: UserCreate, request: Request, authed_user=Depends(admin_required),
               redis_client=Depends(get_redis), pwd_context=Depends(get_pwd_context)):
    # Set user_id, is atomic in redis
    user_id = str(uuid.uuid4()) # https://en.wikipedia.org/wiki/Universally_unique_identifier#Random_UUID_probability_of_duplicates
    success = redis_client.set(f"username:{user.username}", user_id, nx=True)
    if not success:
        raise HTTPException(status_code=400, detail="Username already in use.")
    success = redis_client.set(f"student_id:{user.student_id}", user_id, nx=True)
    if not success:
        raise HTTPException(status_code=400, detail="Student ID already in use.")
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

@router.get("/{id}")
def get_user(id: str, request: Request, redis_client=Depends(get_redis)):
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

@router.patch("/{id}")
def patch_user(id: str, user: UserEdit, request: Request, redis_client=Depends(get_redis), pwd_context=Depends(get_pwd_context)):
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
    # check that user we're changing actually exists
    user_data = redis_client.hgetall(f"user:{id}")
    if not user_data:
        raise HTTPException(status_code=404, detail="User does not exist.")
    if user.username:
        # check that username is actually available
        success = redis_client.set(f"username:{user.username}", id, nx=True)
        if not success:
            raise HTTPException(status_code=400, detail="Username already in use.")
        # delete old username -> id record if exists
        if (old_username:=user_data.get("username")):
            redis_client.delete(f"username:{old_username}")
        # update user record
        redis_client.hset(f"user:{id}", "username", user.username)
    if user.password:
        hashed = pwd_context.hash(user.password)
        redis_client.hset(f"user:{id}", "password_hash", hashed)
    if user.student_id:
        redis_client.hset(f"user:{id}", "student_id", user.student_id)
    return {"status": "success"}

@router.delete("/{id}")
def delete_user(id: str, request: Request, redis_client=Depends(get_redis)):
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


